# Documentation Plugin

The Documentation Plugin for VMPilot helps users create and maintain clear, concise, and factual documentation following best practices for technical writing and working with the MkDocs documentation system.

## Overview

Technical documentation is essential for project usability, but creating effective documentation can be challenging. The Documentation Plugin provides guidance for creating documentation that is:

- Clear and concise
- Factual and straightforward
- Properly structured
- Easy to navigate and understand
- Free of marketing language and exaggerated claims

## Features

The Documentation Plugin offers assistance with:

- Creating new documentation pages
- Structuring content effectively
- Applying plain language principles
- Working with MkDocs features
- Formatting content for readability
- Avoiding common documentation pitfalls

## VMPilot Documentation System

VMPilot uses MkDocs with the Material theme for its documentation system:

- **Configuration**: Located at `/home/dror/vmpilot/mkdocs.yml`
- **Source files**: Markdown files in the `/home/dror/vmpilot/docs/source` directory
- **Navigation**: Defined in the `nav` section of the MkDocs configuration file

### Documentation Structure

- Main documentation pages are in the root of `docs/source`
- Examples are in the `docs/source/examples` directory
- Plugin documentation is in the `docs/source/plugins` directory
- Assets and images are stored in their respective directories

## Documentation Guidelines

### Avoid Marketing Language

Good documentation focuses on facts rather than hype:

- Describe functionality accurately without embellishment
- Avoid superlatives like "revolutionary," "groundbreaking," or "best-in-class"
- Focus on what the project does, not how amazing it allegedly is
- Use objective descriptions rather than subjective praise

### Content Structure

- Put the most important information first, followed by details
- Organize content around user tasks, not system organization
- Use descriptive section headings that convey meaning
- Limit content to three or fewer levels of hierarchy per page
- Ensure each page stands on its own with proper context

### Writing Style

- Use the imperative form (e.g., "Click Save" instead of "You should click Save")
- Use second person (e.g., "you" and "your") for instructions
- Use active voice with strong verbs (e.g., "We mailed your form" not "Your form was mailed")
- Use conversational tone and contractions (e.g., "we're" instead of "we are")
- Eliminate unnecessary words and be concise

### Formatting for Readability

- Create short paragraphs (5-7 lines maximum)
- Use lists and bullets for easy scanning
- Separate content into small, digestible chunks
- Use white space generously to improve scan-ability

## MkDocs Features

The plugin can help you leverage MkDocs features to enhance documentation readability:

- Code blocks with syntax highlighting
- Admonitions (notes, warnings, tips)
- Tables for organized data presentation
- Tabs for alternative content views

## Usage Examples

### Converting Passive to Active Voice

```
Passive: "The configuration file is modified by the system when errors are detected."
Active: "The system modifies the configuration file when it detects errors."
```

### Making Text Concise

```
Wordy: "In the event that you would like to make changes to your account settings, you can navigate to the account settings page where you will find a variety of different options."
Concise: "To change your account settings, go to the Settings page."
```

### Creating Scannable Content

```
Original paragraph:
"The installation process requires several prerequisites including Python 3.8 or higher, pip package manager, and at least 2GB of RAM. You'll also need to ensure you have administrator privileges on your system before beginning the installation. The installation can take approximately 10-15 minutes depending on your internet connection speed."

Scannable version:
"Before installation, ensure you have:
- Python 3.8 or higher
- pip package manager
- 2GB RAM minimum
- Administrator privileges

Installation time: 10-15 minutes (varies with internet speed)"
```
