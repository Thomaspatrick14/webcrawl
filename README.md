#Overview
This Python script runs on AWS to continuously monitor a property rental website for available properties in a particular city. When new properties become available, it sends instant notifications via Telegram, helping users secure accommodation quickly in a competitive rental market.

#Key Features
AWS-Powered Monitoring: Runs 24/7 on Amazon Web Services for reliable property tracking
Real-time Notifications: Delivers instant Telegram alerts when properties appear or disappear
Resilient Operation: Handles network issues, 502 errors, and page load failures with automatic recovery
Anti-Detection Mechanisms: Uses randomized polling intervals and browser fingerprinting to maintain service

#Technical Details
Deployed on AWS EC2 for consistent uptime and performance
Uses headless Chrome browser via Selenium WebDriver for efficient web scraping
Implements intelligent page load detection with retry mechanisms
Stores property data in persistent JSON file between monitoring sessions
Handles service interruptions with automatic restart capabilities

#Setup Requirements
AWS EC2 instance (Linux)
Python 3.6+
Chrome browser and ChromeDriver installed on the instance
Required Python packages: selenium, beautifulsoup4, requests
Telegram bot token and chat ID configuration

#Deployment
Configure your Telegram bot token and chat ID in the script
Update the ChromeDriver path for your AWS environment
Deploy to EC2 instance
Set up as a service for automatic startup

Perfect for students and professionals searching for housing in Eindhoven through rental housing platforms without needing to constantly refresh the website.
