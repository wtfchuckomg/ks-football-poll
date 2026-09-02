# KS Football Media Rankings — setup guide

This is a static site (`index.html`) with no build step. It stores everything
in Firebase (Firestore for data, Firebase Authentication for the admin login)
and is meant to be hosted for free on GitHub Pages, with your GoDaddy domain
pointed at it.

Nobody needs a Claude, Google, or GitHub account to vote or view results —
only you (the admin) need to sign in, to set the current week, release
results, and enter team records.

## 1. Create a Firebase project

1. Go to https://console.firebase.google.com and click **Add project**.
   Free ("Spark") plan is enough — no credit card required.
2. Inside the project, click the **`</>`** (web) icon to register a web app.
   Give it any nickname. You don't need Firebase Hosting here — skip that
   checkbox.
3. Firebase shows you a `firebaseConfig` object. Copy the values into
   `index.html`, near the top of the `<script type="module">` block:

   ```js
   const firebaseConfig = {
     apiKey: "...",
     authDomain: "...",
     projectId: "...",
     storageBucket: "...",
     messagingSenderId: "...",
     appId: "..."
   };
   ```

## 2. Turn on Firestore

1. In the Firebase console, go to **Build > Firestore Database > Create database**.
2. Choose **Production mode** (not test mode) and pick any region.
3. Once created, go to the **Rules** tab and replace the contents with the
   contents of `firestore.rules` from this folder, then click **Publish**.

## 3. Turn on the admin login

1. Go to **Build > Authentication > Get started**.
2. Under **Sign-in method**, enable **Email/Password**.
3. Go to the **Users** tab and click **Add user**. Enter the email and
   password you (the admin) want to sign in with on the site's Admin panel.
   You can add more than one admin user later the same way.

That's it on the Firebase side — no server code, no Cloud Functions, nothing
to deploy from a terminal.

## 4. Push this folder to GitHub

From inside this folder:

```bash
git init
git add index.html firestore.rules README.md
git commit -m "Initial site"
```

Then create a new repository on GitHub (github.com/new — no README/license,
you already have files), and push:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 5. Turn on GitHub Pages

1. On the repo's GitHub page, go to **Settings > Pages**.
2. Under **Build and deployment > Source**, choose **Deploy from a branch**.
3. Branch: `main`, folder: `/ (root)`. Save.
4. GitHub will give you a URL like `https://<your-username>.github.io/<repo-name>/`
   — wait a minute or two, then check that it loads.

## 6. Point your GoDaddy domain at it

1. Still on **Settings > Pages**, under **Custom domain**, enter your domain
   (e.g. `ksfootballpoll.com`) and save. GitHub will show you the DNS records
   it needs.
2. In GoDaddy, go to your domain's **DNS Management** and add:
   - Four **A records** for `@` pointing to GitHub Pages' IPs:
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - A **CNAME record** for `www` pointing to `<your-username>.github.io`
3. DNS changes can take anywhere from a few minutes to a few hours to
   propagate. Once GitHub shows a green checkmark next to your domain on the
   Pages settings page, check **Enforce HTTPS**.

## Using the site

- **Cast a ballot** — voters enter an email (used only to identify their own
  ballot so they can update it later — it's hashed, never stored in plain
  text) and rank 10 schools per class. Classes unlock in order (6A → 5A → ...)
  as each is completed.
- **Public results** — anyone can view this tab. Results for a week only show
  once you (the admin) release that week.
- **Admin** — click "Admin" at the bottom, sign in with the email/password
  you created in step 3, then:
  - **Set week** — changes which week new ballots are recorded under.
  - **Release** — makes a week's results visible on the Public results tab.
  - **Save records** — enter each school's W-L record for a given week/class,
    shown next to their name on the public page.

## Editing team lists / classes

The full list of classes and schools lives near the top of the `<script>`
block in `index.html`, in the `CLASSES` object and `CLASS_ORDER` array — edit
those directly and push the change to GitHub; the live site updates within a
minute or two of GitHub Pages rebuilding.

## A note on trust

Voting here works the same way it did in the original prototype: a ballot is
tied to an email address, but nothing verifies the person submitting it is
actually the owner of that inbox — anyone who knows (or guesses) a voter's
email could overwrite their ballot. That's an acceptable tradeoff for a small,
known panel of voters (media/coaches), but don't publicize this as
tamper-proof. If you eventually want real per-voter authentication, that's a
bigger change (e.g. sending each voter a magic sign-in link) — ask if you want
to go that route later.
