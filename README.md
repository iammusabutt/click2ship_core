# Click2Ship Core

`click2ship_core` is a custom Frappe/ERPNext application that powers core functionality for the Click2Ship stack, extending ERPNext with project-specific features and customizations.

This README explains how to install and work with the app in your Frappe/ERPNext bench.

---

## Requirements

Before installing `click2ship_core`, make sure you have:

- A working **Frappe/ERPNext bench** (development or production)
- At least one site already created (for example: `click2ship.net` or `click2ship.local`)
- Compatible Python / Node / Redis versions for your ERPNext/Frappe version
- Shell/SSH access to the server where the bench is running
- Git access to the repository for `click2ship_core`

---

## Installation

These steps assume you already have ERPNext and Frappe installed on a bench.

### 1. Go to your bench folder

On your server or development machine, open a terminal and go to your bench directory:

```bash
cd ~/frappe-bench
```

Adjust the path if your bench directory is located elsewhere.

---

### 2. Get the app

Use `bench get-app` to download the app into your bench:

```bash
bench get-app click2ship_core git@github.com:your-org/click2ship_core.git
```
Or

```bash
bench get-app click2ship_core https://github.com/your-org/click2ship_core.git
```

---

### 3. Install the app on your site

Install `click2ship_core` on the site where you want it to be available.

```bash
bench --site your-site-name install-app click2ship_core
```

For example, if your site inside bench is named `click2ship.net`:

```bash
bench --site click2ship.net install-app click2ship_core
```

> Note: The **bench site name** is not always the same as the domain name.  
> You can list your sites with:
>
> ```bash
> bench list-sites
> ```

---

### 4. Run migrations and restart

After installation, apply database migrations and restart bench services:

```bash
bench migrate
bench restart
```

On production setups (with supervisor/nginx), follow your usual deployment/restart procedure.

---

### 5. Verify installation

1. Open your ERPNext site in the browser:

   ```text
   https://click2ship.net
   ```

   (or whichever domain points to your ERPNext site)

2. Log in as **Administrator** or a user with sufficient permissions.
3. Check the Desk for `Click2Ship Core` (or similarly named) module, doctypes, and pages provided by this app.
4. Watch the browser console and server logs for any errors when loading pages related to `click2ship_core`.

---

## Configuration

Depending on how your deployment is set up, `click2ship_core` may require some initial configuration after installation. Typical configuration steps include:

- Assigning **roles and permissions** for new doctypes
- Granting users access to the **Click2Ship Core** module or workspace
- Setting any app-specific **settings doctypes** (if implemented), such as:
  - Default Company
  - Default Warehouse
  - External API keys or tokens

If a dedicated settings doctype exists, you can usually find it under:

> **Click2Ship Core → Settings**  
> or  
> **Settings → Click2Ship Core Settings**

Fill in the required fields and save.

---

## Usage

Once installed and configured, users will typically:

- Access the **Click2Ship Core** module from the ERPNext Desk
- Create and manage records in doctypes provided by `click2ship_core`
- Use any reports, dashboards, or custom pages included in the app

You can extend this section with detailed user workflows, screenshots, or links to internal documentation as needed.

---

## Development Setup

If you are developing or customizing `click2ship_core`, follow these steps in a development environment:

1. Start bench:

   ```bash
   cd ~/frappe-bench
   bench start
   ```

2. Ensure the app is installed on your development site:

   ```bash
   bench --site your-dev-site install-app click2ship_core
   bench --site your-dev-site migrate
   ```

3. The app source code is located at:

   ```text
   apps/click2ship_core/
   ```

4. After making code changes, you can clear cache:

   ```bash
   bench clear-cache
   bench clear-website-cache
   ```

5. For build-related changes (JS, CSS, etc.), you may need to run:

   ```bash
   bench build
   bench restart
   ```

---

## Troubleshooting

### App not visible in the Desk

- Confirm the app is installed on the site:

  ```bash
  bench --site your-site-name list-apps
  ```

- Ensure the user has appropriate **roles** and **permissions**.
- Check workspace/module configuration to ensure the module is not hidden.

---

### Migration or install errors

- Run migrate and inspect the output:

  ```bash
  bench --site your-site-name migrate
  ```

- Check log files in the `logs/` directory of the bench.
- Make sure all doctypes, patches, and Python modules in `click2ship_core` load correctly without import errors.

---

### Background jobs / queues

If `click2ship_core` uses background jobs:

```bash
bench --site your-site-name doctor
bench --site your-site-name enqueue-jobs
```

Check that workers are running:

```bash
bench worker
```

---

## Contributing

If you are contributing to `click2ship_core`:

1. Fork the repository.
2. Create a new feature branch:

   ```bash
   git checkout -b feature/my-feature
   ```

3. Commit your changes:

   ```bash
   git commit -m "Add my feature"
   ```

4. Push the branch:

   ```bash
   git push origin feature/my-feature
   ```

5. Open a Pull Request to the main repository.

You can add project-specific coding standards, testing instructions, or CI information here.

---

## License

Specify the license used for `click2ship_core` here, for example:

```text
MIT License
```

or

```text
Proprietary - All rights reserved.
```

Ensure this matches the `LICENSE` file in your repository.

---

## Support / Contact

For questions, support, or deployment-related issues for `click2ship_core` and the Click2Ship ERPNext setup, please use your standard support channels. For example:

- Website: https://drcodex.com
- Email: iammusabutt@gmail.com
- Issue Tracker: URL of your Git repository issues page
