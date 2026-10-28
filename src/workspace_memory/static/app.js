<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>WORKSPACE Memory</title>
    <link rel="stylesheet" href="/static/styles.css" />
  </head>
  <body>
    <div class="app-shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">PERSONAL MEMORY</p>
          <h1>WORKSPACE</h1>
        </div>
        <div>
          <a href="/profile" class="inline-link">Profile</a>
          <a href="/api/auth/logout" class="inline-link">Logout</a>
          <button id="theme-toggle" class="ghost-btn">🌙 Dark</button>
        </div>
      </header>

      <main class="content">
        <section class="hero panel">
          <div>
            <p class="label">Memory dashboard</p>
            <h2>Context that survives resets.</h2>
            <p>Signed in as <strong>{{ profile.display_name or profile.username }}</strong></p>
          </div>
          <div class="stats-grid">
            <div class="stat-box">
              <span id="note-count">0</span>
              <small>Notes</small>
            </div>
            <div class="stat-box">
              <span id="task-count">0</span>
              <small>Tasks</small>
            </div>
            <div class="stat-box">
              <span id="category-count">0</span>
              <small>Categories</small>
            </div>
          </div>
        </section>

        <section class="panel forms-panel">
          <div class="form-card">
            <h3>New note</h3>
            <form id="note-form">
              <textarea name="text" rows="4" placeholder="Write a note..." required></textarea>
              <div class="meta-row">
                <input type="text" name="category" value="general" placeholder="Category" />
                <input type="text" name="tags" placeholder="tags, comma separated" />
              </div>
              <div class="meta-row">
                <input type="date" name="due_at" />
                <input type="datetime-local" name="reminder_at" />
              </div>
              <div class="meta-row compact">
                <select name="status">
                  <option value="new">new</option>
                  <option value="active">active</option>
                  <option value="done">done</option>
                  <option value="blocked">blocked</option>
                </select>
              </div>
              <button type="submit">Save note</button>
            </form>
          </div>

          <div class="form-card">
            <h3>New task</h3>
            <form id="task-form">
              <textarea name="text" rows="4" placeholder="Add a task..." required></textarea>
              <div class="meta-row">
                <input type="text" name="category" value="todo" placeholder="Category" />
                <input type="text" name="tags" placeholder="tags, comma separated" />
              </div>
              <div class="meta-row">
                <input type="date" name="due_at" />
                <input type="datetime-local" name="reminder_at" />
              </div>
              <div class="meta-row compact">
                <select name="status">
                  <option value="new">new</option>
                  <option value="active">active</option>
                  <option value="done">done</option>
                  <option value="blocked">blocked</option>
                </select>
              </div>
              <button type="submit">Save task</button>
            </form>
          </div>
        </section>

        <section class="panel table-panel">
          <div class="toolbar">
            <input id="search-box" type="text" placeholder="Search entries..." />
            <select id="category-filter">
              <option value="">All categories</option>
            </select>
            <select id="kind-filter">
              <option value="">All types</option>
              <option value="note">Notes</option>
              <option value="task">Tasks</option>
            </select>
            <select id="status-filter">
              <option value="">All statuses</option>
              <option value="new">new</option>
              <option value="active">active</option>
              <option value="done">done</option>
              <option value="blocked">blocked</option>
            </select>
            <select id="sort-by">
              <option value="created_at">Created</option>
              <option value="category">Category</option>
              <option value="status">Status</option>
              <option value="kind">Type</option>
              <option value="due_at">Due date</option>
            </select>
            <select id="order-by">
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
            <button id="refresh-btn" class="secondary-btn">Refresh</button>
            <button id="reset-filters" class="secondary-btn">Reset</button>
          </div>

          <div class="action-row">
            <button id="export-markdown" class="secondary-btn">Export Markdown</button>
            <button id="export-json" class="secondary-btn">Export JSON</button>
            <button id="export-csv" class="secondary-btn">Export CSV</button>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Category</th>
                  <th>Tags</th>
                  <th>Text</th>
                  <th>Due</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="entries-body"></tbody>
            </table>
          </div>
        </section>
      </main>
    </div>

    <div id="editor-modal" class="modal hidden" aria-hidden="true">
      <div class="modal-card">
        <div class="modal-header">
          <h3>Edit entry</h3>
          <button type="button" data-close-modal="true">Close</button>
        </div>
        <form id="edit-form">
          <label>
            <span>Text</span>
            <textarea id="edit-text" name="text" rows="8" required></textarea>
          </label>
          <div class="meta-row">
            <label>
              <span>Category</span>
              <input id="edit-category" name="category" type="text" />
            </label>
            <label>
              <span>Status</span>
              <select id="edit-status" name="status">
                <option value="new">new</option>
                <option value="active">active</option>
                <option value="done">done</option>
                <option value="blocked">blocked</option>
              </select>
            </label>
          </div>
          <div class="meta-row">
            <label>
              <span>Due date</span>
              <input id="edit-due" type="date" name="due_at" />
            </label>
            <label>
              <span>Reminder</span>
              <input id="edit-reminder" type="datetime-local" name="reminder_at" />
            </label>
          </div>
          <label>
            <span>Tags</span>
            <input id="edit-tags" name="tags" type="text" />
          </label>
          <button type="submit">Save changes</button>
        </form>
      </div>
    </div>

    <script src="/static/app.js"></script>
  </body>
</html>
