<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Profile</title>
    <link rel="stylesheet" href="/static/styles.css" />
  </head>
  <body>
    <div class="app-shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">USER PROFILE</p>
          <h1>{{ profile.display_name or profile.username }}</h1>
        </div>
        <div>
          <a href="/" class="inline-link">Dashboard</a>
          <a href="/api/auth/logout" class="inline-link">Logout</a>
        </div>
      </header>

      <main class="content">
        <section class="panel profile-panel">
          <h2>Edit profile</h2>
          <form id="profile-form">
            <label>
              <span>Display name</span>
              <input type="text" name="display_name" value="{{ profile.display_name or '' }}" />
            </label>
            <label>
              <span>Role</span>
              <input type="text" name="role" value="{{ profile.role or 'user' }}" />
            </label>
            <label>
              <span>Bio</span>
              <textarea name="bio" rows="5">{{ profile.bio or '' }}</textarea>
            </label>
            <button type="submit">Save profile</button>
          </form>
        </section>
      </main>
    </div>

    <script>
      const form = document.getElementById('profile-form');
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = {
          display_name: formData.get('display_name') || '',
          role: formData.get('role') || 'user',
          bio: formData.get('bio') || '',
        };
        const response = await fetch('/api/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          alert('Unable to save profile');
          return;
        }
        window.location.reload();
      });
    </script>
  </body>
</html>
