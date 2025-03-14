# Documentation Plugin for VMPilot

A plugin that helps users create and maintain clear, concise, and user-friendly documentation.

## Purpose

Provide guidance for creating effective documentation following best practices for technical writing and plain language principles.

## Documentation Guidelines

### Audience Focus
- Write for our intended audience: developers both new and experienced
- Use language and terms familiar to this audience
- Explain technical concepts at appropriate depth for them

### Content Structure
- Put the most important information first, followed by details
- Organize content around user tasks, not system organization
- Use descriptive section headings that convey meaning
- Limit content to three or fewer levels of hierarchy per page
- Ensure each page stands on its own with proper context

### Writing Style
- Use the imperative form (e.g., "Click Save" instead of "You should click Save")
- Use second person (e.g., "you" and "your") for instructions
- Use "users" (plural) to avoid gender-specific pronouns
- Use active voice with strong verbs (e.g., "We mailed your form" not "Your form was mailed")
- Use conversational tone and contractions (e.g., "we're" instead of "we are")
- Eliminate all unnecessary words and be concise

### Formatting for Readability
- Create short paragraphs (5-7 lines maximum)
- Use lists and bullets for easy scanning
- Separate content into small, digestible chunks
- Use white space generously to improve scan-ability

### Link Text
- Never use "click here" for links
- Link text should describe what users will find at the destination
- Include keywords in link text to help with search engine optimization

## Usage

When a user asks for help with documentation, guide them through:

1. **Determining the purpose**: Help clarify what information needs to be conveyed
2. **Structuring the content**: Suggest appropriate headings and organization
3. **Applying plain language principles**: Edit text to be clear, concise, and active
4. **Enhancing readability**: Format content for easy scanning

## Examples

### Converting passive to active voice
```
Passive: "The configuration file is modified by the system when errors are detected."
Active: "The system modifies the configuration file when it detects errors."
```

### Making text concise
```
Wordy: "In the event that you would like to make changes to your account settings, you can navigate to the account settings page where you will find a variety of different options."
Concise: "To change your account settings, go to the Settings page."
```

### Creating scannable content
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
