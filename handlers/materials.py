"""
Materials Handler — ManyBot-style infinite nested folder system
- mat_nodes = folders (infinite nesting)
- mat_files = files inside folders (PDF/photo/text)
- Pagination for large folders (8 per page)
- Back button auto-added (goes to parent)
- Admin password protected add/edit/delete
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import (
    get_conn, mat_get_children, mat_get_node, mat_get_files,
    mat_add_node, mat_add_file, mat_delete_node, mat_delete_file,
    mat_rename_node, mat_edit_file_title, mat_get_breadcrumb
)
from ui import back_btn, cancel_btn, confirm_delete_kb, E
from handlers.common import check_banned
from config import ADMIN_PASS
import logging

logger = logging.getLogger(__name__)

PAGE = 6   # items per page

# ── States ───────────────────────────────────────────────────────────────────
(
    MAT_ADMIN_PASS,
    MAT_ADD_FOLDER_NAME,
    MAT_ADD_FOLDER_EMOJI,
    MAT_ADD_FILE_TITLE,
    MAT_ADD_FILE_CONTENT,   # waiting for PDF/photo/text
    MAT_RENAME_NODE,
    MAT_EDIT_FILE_TITLE,
) = range(7)

_mat_authed: set = set()   # users who passed admin pass for materials


def _is_mat_admin(tg_id: int) -> bool:
    return tg_id in _mat_authed


# ════════════════════════════════════════════════════════════════════════════
#  VIEWER — Browse folders and files (for all users)
# ════════════════════════════════════════════════════════════════════════════

def _build_folder_kb(node_id, page: int, is_admin: bool):
    """Build keyboard for a folder: sub-folders + files + pagination + back."""
    children = mat_get_children(node_id)    # sub-folders
    files    = mat_get_files(node_id)       # files

    all_items = []
    for ch in children:
        label = f"{ch['emoji']} {ch['name']}"
        cb    = f"mat_node_{ch['id']}_p1"
        all_items.append(("folder", label, cb))
    for f in files:
        label = f"📄 {f['title'] or 'File'}"
        cb    = f"mat_file_{f['id']}"
        all_items.append(("file", label, cb))

    total       = len(all_items)
    total_pages = max(1, (total + PAGE - 1) // PAGE)
    page        = max(1, min(page, total_pages))
    page_items  = all_items[(page-1)*PAGE : page*PAGE]

    kb_rows = []
    for kind, label, cb in page_items:
        kb_rows.append([Btn(label, callback_data=cb)])

    # Pagination row
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(Btn("⬅️", callback_data=f"mat_node_{node_id}_p{page-1}"))
        nav.append(Btn(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav.append(Btn("➡️", callback_data=f"mat_node_{node_id}_p{page+1}"))
        kb_rows.append(nav)

    # Admin controls row
    if is_admin:
        kb_rows.append([
            Btn("➕ Add Folder", callback_data=f"mat_adm_addfolder_{node_id}"),
            Btn("📤 Add File",   callback_data=f"mat_adm_addfile_{node_id}"),
        ])
        kb_rows.append([
            Btn("✏️ Rename",    callback_data=f"mat_adm_rename_{node_id}"),
            Btn("🗑️ Delete",    callback_data=f"mat_adm_delete_{node_id}"),
        ])
        kb_rows.append([Btn("📋 Manage Files", callback_data=f"mat_adm_files_{node_id}_p1")])

    # Back button
    node = mat_get_node(node_id)
    if node and node.get("parent_id") is not None:
        parent_id = node["parent_id"]
        kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"mat_node_{parent_id}_p1")])
    else:
        kb_rows.append([Btn(f"{E['back']} Back", callback_data="materials_home")])

    return Markup(kb_rows), total, total_pages


async def materials_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top-level folders."""
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END

    is_admin   = _is_mat_admin(update.effective_user.id)
    top_nodes  = mat_get_children(None)   # parent_id IS NULL

    kb_rows = []
    for n in top_nodes:
        kb_rows.append([Btn(f"{n['emoji']} {n['name']}", callback_data=f"mat_node_{n['id']}_p1")])

    if is_admin:
        kb_rows.append([Btn("➕ Add Top-Level Folder", callback_data="mat_adm_addfolder_root")])

    if not is_admin:
        kb_rows.append([Btn("🔑 Admin Mode",  callback_data="mat_admin_login")])
    else:
        kb_rows.append([Btn("🔓 Admin Mode ✓", callback_data="mat_admin_logout")])

    kb_rows.append([Btn(f"{E['back']} Back", callback_data="home")])

    await query.edit_message_text(
        "📚 *Materials*\n\nChoose a section:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mat_open_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open a folder — mat_node_{id}_p{page}."""
    query = update.callback_query
    await query.answer()
    parts   = query.data.split("_")   # mat, node, {id}, p{page}
    node_id = int(parts[2])
    page    = int(parts[3].replace("p", ""))

    node = mat_get_node(node_id)
    if not node:
        await query.edit_message_text("Folder not found.", reply_markup=back_btn("materials_home"))
        return ConversationHandler.END

    is_admin = _is_mat_admin(update.effective_user.id)
    kb, total, total_pages = _build_folder_kb(node_id, page, is_admin)

    # Breadcrumb
    crumbs = mat_get_breadcrumb(node_id)
    crumb_text = " › ".join(c["name"] for c in crumbs)

    if total == 0 and not is_admin:
        text = f"📁 *{node['emoji']} {node['name']}*\n_{crumb_text}_\n\nThis folder is empty."
    else:
        children_count = len(mat_get_children(node_id))
        files_count    = len(mat_get_files(node_id))
        text = (
            f"📁 *{node['emoji']} {node['name']}*\n"
            f"_{crumb_text}_\n\n"
            f"📂 {children_count} sub-folder(s)  •  📄 {files_count} file(s)"
        )

    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def mat_send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a file to user — mat_file_{id}."""
    query = update.callback_query
    await query.answer()
    file_id_int = int(query.data.split("_")[2])

    conn  = get_conn()
    f     = conn.execute("SELECT * FROM mat_files WHERE id=?", (file_id_int,)).fetchone()
    conn.close()

    if not f:
        await query.answer("File not found.", show_alert=True)
        return ConversationHandler.END

    node_id = f["node_id"]
    caption = f["title"] or "File"

    try:
        if f["file_type"] == "pdf":
            await context.bot.send_document(
                update.effective_user.id,
                document=f["file_id"],
                caption=f"📄 *{caption}*", parse_mode="Markdown"
            )
        elif f["file_type"] == "photo":
            await context.bot.send_photo(
                update.effective_user.id,
                photo=f["file_id"],
                caption=f"🖼 *{caption}*", parse_mode="Markdown"
            )
        elif f["file_type"] == "text":
            await context.bot.send_message(
                update.effective_user.id,
                f"📝 *{caption}*\n\n{f['content']}", parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"File send error: {e}")
        await context.bot.send_message(update.effective_user.id, "❌ Could not send file.")

    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN LOGIN / LOGOUT
# ════════════════════════════════════════════════════════════════════════════
async def mat_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔑 Enter admin password to unlock Materials editing:",
        reply_markup=cancel_btn("materials_home")
    )
    return MAT_ADMIN_PASS


async def mat_admin_got_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == ADMIN_PASS:
        _mat_authed.add(update.effective_user.id)
        await update.message.reply_text(
            "✅ Admin mode activated! You can now add, edit and delete folders and files.",
            reply_markup=Markup([[Btn("📚 Open Materials", callback_data="materials_home")]])
        )
    else:
        await update.message.reply_text(
            "❌ Wrong password.",
            reply_markup=Markup([[Btn("↩️ Back", callback_data="materials_home")]])
        )
    return ConversationHandler.END


async def mat_admin_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Admin mode deactivated.")
    _mat_authed.discard(update.effective_user.id)
    query.data = "materials_home"
    return await materials_home(update, context)


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN — ADD FOLDER
# ════════════════════════════════════════════════════════════════════════════
async def mat_adm_addfolder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_addfolder_{node_id|root}"""
    query = update.callback_query
    await query.answer()
    if not _is_mat_admin(update.effective_user.id):
        await query.answer("Login as admin first.", show_alert=True)
        return ConversationHandler.END

    raw = query.data.split("_")[-1]
    parent_id = None if raw == "root" else int(raw)
    context.user_data["mat_add_folder_parent"] = parent_id

    if parent_id is None:
        loc = "top-level (Materials home)"
    else:
        node = mat_get_node(parent_id)
        loc  = f"inside *{node['name']}*" if node else "selected folder"

    await query.edit_message_text(
        f"➕ *Add Folder*\n\nLocation: {loc}\n\nSend folder name:",
        reply_markup=cancel_btn("materials_home"), parse_mode="Markdown"
    )
    return MAT_ADD_FOLDER_NAME


async def mat_adm_got_folder_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mat_add_folder_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Now send an emoji for this folder (e.g. `📗` `🧪` `🔥`) or type `skip` for default 📁:",
        reply_markup=cancel_btn("materials_home"), parse_mode="Markdown"
    )
    return MAT_ADD_FOLDER_EMOJI


async def mat_adm_got_folder_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt   = update.message.text.strip()
    emoji = "📁" if txt.lower() == "skip" else txt
    name  = context.user_data.get("mat_add_folder_name", "Folder")
    pid   = context.user_data.get("mat_add_folder_parent")

    nid = mat_add_node(pid, name, emoji)
    if pid is None:
        back_cb = "materials_home"
    else:
        back_cb = f"mat_node_{pid}_p1"

    await update.message.reply_text(
        f"✅ Folder *{emoji} {name}* created!",
        reply_markup=Markup([
            [Btn("📂 Open Folder",   callback_data=f"mat_node_{nid}_p1"),
             Btn("➕ Add Another",   callback_data=f"mat_adm_addfolder_{pid if pid else 'root'}")],
            [Btn(f"{E['back']} Back", callback_data=back_cb)],
        ]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN — ADD FILE
# ════════════════════════════════════════════════════════════════════════════
async def mat_adm_addfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_addfile_{node_id}"""
    query = update.callback_query
    await query.answer()
    if not _is_mat_admin(update.effective_user.id):
        await query.answer("Login as admin first.", show_alert=True)
        return ConversationHandler.END

    node_id = int(query.data.split("_")[-1])
    node    = mat_get_node(node_id)
    context.user_data["mat_add_file_node"] = node_id

    await query.edit_message_text(
        f"📤 *Add File* to *{node['name'] if node else 'folder'}*\n\n"
        f"Enter a *title/name* for this file:",
        reply_markup=cancel_btn(f"mat_node_{node_id}_p1"), parse_mode="Markdown"
    )
    return MAT_ADD_FILE_TITLE


async def mat_adm_got_file_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mat_add_file_title"] = update.message.text.strip()
    node_id = context.user_data.get("mat_add_file_node")
    await update.message.reply_text(
        "Now send the file:\n"
        "• *PDF* — send as document\n"
        "• *Photo/Image* — send as photo\n"
        "• *Text* — just type the text\n\n"
        "_(You can send multiple files one by one — tap Done when finished)_",
        reply_markup=Markup([[Btn("✅ Done", callback_data=f"mat_adm_filedone_{node_id}")]]),
        parse_mode="Markdown"
    )
    context.user_data["mat_add_file_count"] = 0
    return MAT_ADD_FILE_CONTENT


async def mat_adm_got_file_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    node_id = context.user_data.get("mat_add_file_node")
    title   = context.user_data.get("mat_add_file_title", "File")
    count   = context.user_data.get("mat_add_file_count", 0)

    if update.message.document:
        mat_add_file(node_id, title, "pdf", file_id=update.message.document.file_id)
        count += 1
        context.user_data["mat_add_file_count"] = count
        await update.message.reply_text(
            f"✅ PDF {count} saved! Send more or tap Done.",
            reply_markup=Markup([[Btn("✅ Done", callback_data=f"mat_adm_filedone_{node_id}")]])
        )
    elif update.message.photo:
        mat_add_file(node_id, title, "photo", file_id=update.message.photo[-1].file_id)
        count += 1
        context.user_data["mat_add_file_count"] = count
        await update.message.reply_text(
            f"✅ Photo {count} saved! Send more or tap Done.",
            reply_markup=Markup([[Btn("✅ Done", callback_data=f"mat_adm_filedone_{node_id}")]])
        )
    elif update.message.text:
        mat_add_file(node_id, title, "text", content=update.message.text.strip())
        count += 1
        context.user_data["mat_add_file_count"] = count
        await update.message.reply_text(
            f"✅ Text {count} saved! Send more or tap Done.",
            reply_markup=Markup([[Btn("✅ Done", callback_data=f"mat_adm_filedone_{node_id}")]])
        )
    return MAT_ADD_FILE_CONTENT


async def mat_adm_filedone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    node_id = int(query.data.split("_")[-1])
    count   = context.user_data.get("mat_add_file_count", 0)

    if count == 0:
        await query.edit_message_text(
            "⚠️ No files added yet. Send at least one file.",
            reply_markup=Markup([[Btn("❌ Cancel", callback_data=f"mat_node_{node_id}_p1")]])
        )
        return MAT_ADD_FILE_CONTENT

    await query.edit_message_text(
        f"✅ {count} file(s) added to folder!",
        reply_markup=Markup([
            [Btn("📂 View Folder",   callback_data=f"mat_node_{node_id}_p1"),
             Btn("📤 Add More Files", callback_data=f"mat_adm_addfile_{node_id}")],
        ])
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN — RENAME FOLDER
# ════════════════════════════════════════════════════════════════════════════
async def mat_adm_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_rename_{node_id}"""
    query = update.callback_query
    await query.answer()
    if not _is_mat_admin(update.effective_user.id):
        await query.answer("Login as admin first.", show_alert=True)
        return ConversationHandler.END

    node_id = int(query.data.split("_")[-1])
    node    = mat_get_node(node_id)
    context.user_data["mat_rename_node"] = node_id

    await query.edit_message_text(
        f"✏️ *Rename Folder*\n\nCurrent: *{node['emoji']} {node['name']}*\n\n"
        f"Send new name (include emoji at start if you want, e.g. `📗 Class 11`):",
        reply_markup=cancel_btn(f"mat_node_{node_id}_p1"), parse_mode="Markdown"
    )
    return MAT_RENAME_NODE


async def mat_adm_got_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt     = update.message.text.strip()
    node_id = context.user_data.get("mat_rename_node")
    # Try to split emoji from name
    parts   = txt.split(" ", 1)
    if len(parts) == 2 and len(parts[0]) <= 4:
        emoji, name = parts[0], parts[1]
    else:
        emoji, name = None, txt
    mat_rename_node(node_id, name, emoji)
    node = mat_get_node(node_id)
    await update.message.reply_text(
        f"✅ Renamed to *{node['emoji']} {node['name']}*!",
        reply_markup=Markup([[Btn("📂 View Folder", callback_data=f"mat_node_{node_id}_p1")]]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN — DELETE FOLDER
# ════════════════════════════════════════════════════════════════════════════
async def mat_adm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_delete_{node_id}"""
    query = update.callback_query
    await query.answer()
    if not _is_mat_admin(update.effective_user.id):
        await query.answer("Login as admin first.", show_alert=True)
        return ConversationHandler.END

    node_id  = int(query.data.split("_")[-1])
    node     = mat_get_node(node_id)
    parent_id = node.get("parent_id") if node else None
    back_cb  = f"mat_node_{parent_id}_p1" if parent_id else "materials_home"

    await query.edit_message_text(
        f"⚠️ *Cannot be undone!*\nDelete folder *{node['emoji']} {node['name']}* and ALL its contents?",
        reply_markup=confirm_delete_kb(
            f"mat_adm_del_yes_{node_id}",
            f"mat_node_{node_id}_p1"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mat_adm_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    node_id  = int(query.data.split("_")[-1])
    node     = mat_get_node(node_id)
    parent_id = node.get("parent_id") if node else None
    mat_delete_node(node_id)
    back_cb  = f"mat_node_{parent_id}_p1" if parent_id else "materials_home"
    await query.edit_message_text(
        "🗑️ Folder deleted.",
        reply_markup=back_btn(back_cb)
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN — MANAGE FILES in a folder
# ════════════════════════════════════════════════════════════════════════════
async def mat_adm_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_files_{node_id}_p{page} — list files with edit/delete options."""
    query = update.callback_query
    await query.answer()
    parts   = query.data.split("_")
    node_id = int(parts[3])
    page    = int(parts[4].replace("p", ""))

    files = mat_get_files(node_id)
    node  = mat_get_node(node_id)

    if not files:
        await query.edit_message_text(
            "No files in this folder yet.",
            reply_markup=Markup([
                [Btn("📤 Add File",   callback_data=f"mat_adm_addfile_{node_id}")],
                [Btn(f"{E['back']} Back", callback_data=f"mat_node_{node_id}_p1")],
            ])
        )
        return ConversationHandler.END

    total       = len(files)
    total_pages = max(1, (total + PAGE - 1) // PAGE)
    page        = max(1, min(page, total_pages))
    page_files  = files[(page-1)*PAGE : page*PAGE]

    kb_rows = []
    for f in page_files:
        type_icon = {"pdf": "📄", "photo": "🖼", "text": "📝"}.get(f["file_type"], "📁")
        kb_rows.append([
            Btn(f"{type_icon} {f['title'] or 'untitled'}", callback_data="noop"),
            Btn("✏️", callback_data=f"mat_adm_editfile_{f['id']}"),
            Btn("🗑️", callback_data=f"mat_adm_delfile_confirm_{f['id']}_{node_id}"),
        ])

    nav = []
    if page > 1:
        nav.append(Btn("⬅️", callback_data=f"mat_adm_files_{node_id}_p{page-1}"))
    nav.append(Btn(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(Btn("➡️", callback_data=f"mat_adm_files_{node_id}_p{page+1}"))
    if len(nav) > 1:
        kb_rows.append(nav)

    kb_rows.append([
        Btn("📤 Add File",    callback_data=f"mat_adm_addfile_{node_id}"),
        Btn(f"{E['back']} Back", callback_data=f"mat_node_{node_id}_p1"),
    ])

    await query.edit_message_text(
        f"📋 *Files in {node['name'] if node else 'folder'}*\n_{total} file(s), page {page}/{total_pages}_",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mat_adm_editfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_editfile_{file_id}"""
    query = update.callback_query
    await query.answer()
    file_id_int = int(query.data.split("_")[-1])
    conn = get_conn()
    f    = conn.execute("SELECT * FROM mat_files WHERE id=?", (file_id_int,)).fetchone()
    conn.close()
    if not f:
        await query.answer("Not found.", show_alert=True)
        return ConversationHandler.END
    context.user_data["mat_edit_file_id"]   = file_id_int
    context.user_data["mat_edit_file_node"] = f["node_id"]
    await query.edit_message_text(
        f"✏️ *Edit File Title*\n\nCurrent: *{f['title'] or 'untitled'}*\n\nSend new title:",
        reply_markup=cancel_btn(f"mat_adm_files_{f['node_id']}_p1"), parse_mode="Markdown"
    )
    return MAT_EDIT_FILE_TITLE


async def mat_adm_got_edit_file_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_title   = update.message.text.strip()
    file_id_int = context.user_data.get("mat_edit_file_id")
    node_id     = context.user_data.get("mat_edit_file_node")
    mat_edit_file_title(file_id_int, new_title)
    await update.message.reply_text(
        f"✅ Title updated to: *{new_title}*",
        reply_markup=Markup([[Btn("📋 View Files", callback_data=f"mat_adm_files_{node_id}_p1")]]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mat_adm_delfile_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_delfile_confirm_{file_id}_{node_id}"""
    query = update.callback_query
    await query.answer()
    parts       = query.data.split("_")
    file_id_int = int(parts[4])
    node_id     = int(parts[5])
    conn = get_conn()
    f    = conn.execute("SELECT * FROM mat_files WHERE id=?", (file_id_int,)).fetchone()
    conn.close()
    await query.edit_message_text(
        f"⚠️ Delete file *{f['title'] if f else 'this file'}*?",
        reply_markup=confirm_delete_kb(
            f"mat_adm_delfile_yes_{file_id_int}_{node_id}",
            f"mat_adm_files_{node_id}_p1"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mat_adm_delfile_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """mat_adm_delfile_yes_{file_id}_{node_id}"""
    query = update.callback_query
    await query.answer()
    parts       = query.data.split("_")
    file_id_int = int(parts[4])
    node_id     = int(parts[5])
    mat_delete_file(file_id_int)
    await query.edit_message_text(
        "🗑️ File deleted.",
        reply_markup=back_btn(f"mat_adm_files_{node_id}_p1")
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  CANCEL
# ════════════════════════════════════════════════════════════════════════════
async def mat_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        update.callback_query.data = "materials_home"
        return await materials_home(update, update._bot_data if hasattr(update, '_bot_data') else None or update.callback_query)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_materials_conv():
    return ConversationHandler(
        entry_points=[
            # User browsing
            CallbackQueryHandler(materials_home,         pattern="^materials_home$"),
            CallbackQueryHandler(mat_open_node,          pattern=r"^mat_node_\d+_p\d+$"),
            CallbackQueryHandler(mat_send_file,          pattern=r"^mat_file_\d+$"),
            # Admin login/logout
            CallbackQueryHandler(mat_admin_login,        pattern="^mat_admin_login$"),
            CallbackQueryHandler(mat_admin_logout,       pattern="^mat_admin_logout$"),
            # Admin actions
            CallbackQueryHandler(mat_adm_addfolder,      pattern=r"^mat_adm_addfolder_(\d+|root)$"),
            CallbackQueryHandler(mat_adm_addfile,        pattern=r"^mat_adm_addfile_\d+$"),
            CallbackQueryHandler(mat_adm_filedone,       pattern=r"^mat_adm_filedone_\d+$"),
            CallbackQueryHandler(mat_adm_rename,         pattern=r"^mat_adm_rename_\d+$"),
            CallbackQueryHandler(mat_adm_delete,         pattern=r"^mat_adm_delete_\d+$"),
            CallbackQueryHandler(mat_adm_del_yes,        pattern=r"^mat_adm_del_yes_\d+$"),
            CallbackQueryHandler(mat_adm_files,          pattern=r"^mat_adm_files_\d+_p\d+$"),
            CallbackQueryHandler(mat_adm_editfile,       pattern=r"^mat_adm_editfile_\d+$"),
            CallbackQueryHandler(mat_adm_delfile_confirm,pattern=r"^mat_adm_delfile_confirm_\d+_\d+$"),
            CallbackQueryHandler(mat_adm_delfile_yes,    pattern=r"^mat_adm_delfile_yes_\d+_\d+$"),
        ],
        states={
            MAT_ADMIN_PASS:       [MessageHandler(filters.TEXT & ~filters.COMMAND, mat_admin_got_pass)],
            MAT_ADD_FOLDER_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, mat_adm_got_folder_name)],
            MAT_ADD_FOLDER_EMOJI: [MessageHandler(filters.TEXT & ~filters.COMMAND, mat_adm_got_folder_emoji)],
            MAT_ADD_FILE_TITLE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, mat_adm_got_file_title)],
            MAT_ADD_FILE_CONTENT: [
                MessageHandler(filters.Document.ALL,             mat_adm_got_file_content),
                MessageHandler(filters.PHOTO,                    mat_adm_got_file_content),
                MessageHandler(filters.TEXT & ~filters.COMMAND,  mat_adm_got_file_content),
                CallbackQueryHandler(mat_adm_filedone, pattern=r"^mat_adm_filedone_\d+$"),
            ],
            MAT_RENAME_NODE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, mat_adm_got_rename)],
            MAT_EDIT_FILE_TITLE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, mat_adm_got_edit_file_title)],
        },
        fallbacks=[
            CallbackQueryHandler(materials_home, pattern="^materials_home$"),
            CommandHandler("start", materials_home),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
