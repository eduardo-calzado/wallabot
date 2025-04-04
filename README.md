<img src="https://i.ibb.co/W4mFFqpG/FDBEC4-CF-569-F-4026-A1-A9-F2-F9197-B5214-2.png" alt="Wallabot Email Notification Sample" width="175px">

# Wallabot

Monitors Wallapop for new listings matching your search criteria and sends email notifications with product images, seller information, and more.

## Features

- 📧 Email alerts for new listings with detailed product information
- 🖼️ Product images directly from the search results
- 👤 Seller information (ratings, sales, location)
- 🚚 Shipping availability status
- 📊 Smart filtering options to focus on high-quality listings
- 📝 Detailed logging for troubleshooting

## Setup Instructions

1. Install the required dependencies:
   ```
   pip3 install selenium webdriver-manager
   ```

2. Edit the `config.py` file with your information:
   - Email settings:
     - For Gmail, create an app password at https://myaccount.google.com/apppasswords
     - Set your sender and receiver email addresses
   - Search settings:
     - Set the search URL from Wallapop (create your search on Wallapop and copy the URL)
     - Configure filters for your search (price, keywords, location)
   - Filter options (see Configuration Options below)

3. Run the bot:
   ```
   python3 wallabot.py
   ```

## Configuration Options

The script includes several options in `config.py` that you can customize:

### Search Configuration

- `OFFERS_URL`: The Wallapop search URL (price range, keywords, location)
- `MAX_ITEMS_TO_CHECK`: Maximum number of listings to check per run (default: 6)

### Filter Options

- `SKIP_RESERVED_ITEMS = True`: Skip items that are marked as reserved
- `SHIPPING_REQUIRED = True`: Only process items with shipping available
- `SKIP_WITH_LESS_THAN_RATING_COUNTER = 3`: Skip sellers with fewer than 3 ratings
- `SKIP_WITH_LESS_THAN_SALES_NUMBER = 5`: Skip sellers with fewer than 5 completed sales

### Logging Options

- `DEBUG = False`: Set to True for verbose logging
- `ENABLE_FILE_LOGGING = True`: Set to False to disable writing logs to file

## Command Line Arguments

- `--visible`: Run in visible browser mode (not headless)
- `--debug`: Enable debug mode with visible browser and 30-second pause
- `--delay=X`: Keep browser open for X seconds after completion (for debugging)

## Email Notifications

The email includes:
- Product image from search results
- Title and price
- Link to the listing
- Seller information with ratings
- Location information
- Shipping availability
- Number of sales

## Testing

The script includes dedicated test files to verify functionality:

- Test email configuration:
  ```
  python3 test_email.py
  ```
  This will send a test email using your configured email settings to verify that authentication and delivery work correctly.

- Test browser functionality:
  ```
  python3 test_browser.py
  ```
  This opens the browser with your search URL to verify that Selenium and browser interaction work correctly.

## Scheduling with Cron (Linux/macOS)

To run the script automatically on a schedule:

1. Make the included script executable:
   ```
   chmod +x run_wallabot.sh
   ```

2. Open your crontab for editing:
   ```
   crontab -e
   ```

3. Add a line to run it at your desired frequency:
   ```
   # Run every hour
   0 * * * * /full/path/to/wallabot-alerts/run_wallabot.sh

   # OR run every 30 minutes
   */30 * * * * /full/path/to/wallabot-alerts/run_wallabot.sh
   ```

## Scheduling with Task Scheduler (Windows)

1. Create a batch file (run_wallabot.bat) with:
   ```
   @echo off
   cd /d C:\path\to\wallabot-alerts
   python wallabot.py >> wallabot.log 2>&1
   ```

2. Open Task Scheduler (search for it in Start menu)
3. Click "Create Basic Task"
4. Give it a name like "Wallabot" and click Next
5. Select how often you want it to run (e.g., Daily) and click Next
6. Set the time and click Next
7. Select "Start a program" and click Next
8. Browse to your batch file and click Next, then Finish

## Automatic Execution with GitHub Actions

You can run Wallabot automatically in the cloud using GitHub Actions:

1. Create a GitHub repository for your Wallabot code
2. Add the following GitHub secrets in your repository settings:
   - `EMAIL_USERNAME`: Your Gmail account
   - `EMAIL_PASSWORD`: Your app password
   - `EMAIL_RECEIVER`: Email that will receive notifications

3. Create a workflow file at `.github/workflows/wallabot.yml` with:
   ```yaml
   name: Run Wallabot

   on:
     schedule:
       - cron: '*/10 * * * *'  # Runs every 10 minutes
     workflow_dispatch:  # Allows manual triggering

   jobs:
     run-wallabot:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         # Restore offers.pickle from cache
         - name: Restore offers cache
           uses: actions/cache@v3
           with:
             path: offers.pickle
             # Use a fixed key that doesn't change with each run
             key: offers-${{ github.repository }}-${{ github.ref }}
             restore-keys: |
               offers-${{ github.repository }}-${{ github.ref }}
               offers-${{ github.repository }}
               offers-
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.10'
             
         - name: Install Chrome
           run: |
             wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
             sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
             sudo apt-get update
             sudo apt-get install -y google-chrome-stable
         
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
         
         - name: Update credentials in config.py
           env:
             EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
             EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
             EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
           run: |
             sed -i "s/username = '.*'/username = '$EMAIL_USERNAME'/" config.py
             sed -i "s/password = '.*'/password = '$EMAIL_PASSWORD'/" config.py
             sed -i "s/receiver = '.*'/receiver = '$EMAIL_RECEIVER'/" config.py
         
         # Create empty pickle file if it doesn't exist
         - name: Ensure pickle file exists
           run: |
             if [ ! -f offers.pickle ]; then
               echo "Creating new offers.pickle file"
               touch offers.pickle
             fi
         
         - name: Run Wallabot
           run: python wallabot.py --headless
           
         # Upload logs as artifacts for inspection
         - name: Upload logs
           uses: actions/upload-artifact@v4
           with:
             name: wallabot-logs
             path: wallabot.log
             retention-days: 7
   ```

4. Push all your code to GitHub
5. GitHub will automatically run Wallabot according to the schedule

This approach has several advantages:
- No need to keep your computer running
- Executes reliably on a schedule in the cloud
- Logs are accessible through GitHub's interface
- You can trigger manual runs through the Actions tab

Note: GitHub's scheduled actions may sometimes be delayed during periods of high GitHub Actions usage.

## Troubleshooting

If you encounter issues:
- Check wallabot.log for detailed error information
- Enable DEBUG=True in config.py for more verbose logging
- Run with `--visible` flag to see the browser in action
- Verify your search URL works in a normal browser
- Check that your app password is correct for Gmail

## Disclaimer
This tool is for personal use only. The author takes no responsibility for any illegal use of this software.

---

Made by @eduardo-calzado with ❤️ for the Python community
