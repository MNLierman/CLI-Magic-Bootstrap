# Magic Bootstraps Repo

Welcome to the Magic Bootstraps repo! This project showcases @MNLierman's latest adventures in script magic auto-selection. The goal is to make running scripts on various systems as seamless as possible using a simple command such as:
  <br><br>**```curl yourname.tld/win-ins | iex```**  OR  **```curl yourname.tld/lin-ins | sh```** <br> <br>
Either of these commands would find and **auto-complete** something like **```win-install-software.ps1```**, pull this script, and run it. This app gives you the ability to host your favorite scripts on GitHub and easily run them without a USB thumbdrive like you'd traditionally have to have. Sure, there are a few repos on here that use something of a 404 approach to find a script, but I don't see this as very versatile or easy to work with. Hosting this yourself is not that hard, as most of the heavy lift is done by GITHUB.

**Below, you'll find detailed information on how this works and how you can contribute.**

## Coding With A Purpose

The ultimate aim of this project is to create a robust and user-friendly system where users/admins can easily run scripts on endpoint devices by simply using a curl or iex command. The simplicity of this allows you to easily share simple URLs with necessary people (even end users). The magic lies in the auto-selection process, which attempts to determine the correct script based on the command you provide. This system is designed to save time and reduce errors, making it easier for anyone to manage and automate tasks on their devices.

## How It Works

### Hosting and Running Scripts

1. **Script Hosting**: All scripts are hosted on GitHub. You can clone the repo and upload your own scripts to it.
2. **Running Scripts**: Use curl or iex to serve up the script you need. For example: ```sh curl name.site/script```
   
The system will attempt to find the closest match to your query and run the appropriate script.

### Setting Up Your Own Server

To use the magic CLI part, you'll need your own server. Here's what you need to do:

1. **Fuzzy Python Script**: The server runs a fuzzy Python script that helps in auto-selecting the correct script.
2. **GitHub API Key**: You'll need a GitHub API key to obtain a directory listing of your scripts for the specified directory.
3. **Clone Your Own Copy**: You will need to clone your own copy of this repo to uplaod your own scripts, etc. If you want, you can make your repo rrivate and then,
4. **Pull & Modify ```settings.conf```**, OR, modify it from within your private repo.
5. **Pull & Run ```setup.sh```**: This will prepare your environment for hosting the CLI Magic Bootstraps app.
6. **Test your app**: While I don't have any specific commands you can run at the moment, I will add a couple of test scripts in the future.
7. **Update your scripts and start using the app!**

### Directory Matching

The directory part of the command must always match and will never be magic. For example, if your targeted script is located at `name.domain/windows/install-software.cmd`, you must get the URL correctly up to about `install-s`, depending on if you have other scripts in the `windows` directory that start with `install`.

### Example

If you have a script located at `name.domain/windows/install-software.cmd`, you would use: ```sh curl name.site/windows/install-s```
The system will then attempt to find and run install-software.cmd or the closest match.

## Contributing

We welcome contributions! Here's how you can help:

1. **Clone the Repo**: Clone the repository to your local machine.
2. **Upload Your Scripts**: Add your own scripts to the repo.
3. **Share Your Work**: Feel free to comment and share what you're working on. Your contributions will help improve the system and make it more versatile.

## Support

If you find this project valuable, please consider making a donation. Your support will enable us to keep this repository up-to-date and continue helping others with their scripting needs.

Thank you for your support!
