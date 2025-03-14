# Documentation Plugin for VMPilot

A plugin that helps users create and maintain clear, concise, and factual documentation

## Purpose

This plugin provides guidance for creating effective documentation following best practices for technical writing and plain language principles, and helps users work with the MkDocs documentation system used by VMPilot. It emphasizes factual, straightforward content that avoids marketing language and exaggerated claims.

## VMPilot Documentation System

### MkDocs Setup
- VMPilot uses MkDocs with the Material theme for documentation
- The configuration file is located at `/home/dror/vmpilot/mkdocs.yml`
- The documentation source files are in Markdown format in the `/home/dror/vmpilot/docs/source` directory
- The navigation structure is defined in the `nav` section of the MkDocs configuration file

### Documentation Structure
- Main documentation pages are in the root of `docs/source`
- Examples are in the `docs/source/examples` directory
- Plugin documentation is in the `docs/source/plugins` directory
- Assets and images are stored in their respective directories

### Working with Documentation
- To add a new page, create a Markdown file in the appropriate directory
- Update the `nav` section in `mkdocs.yml` to include the new page
- To preview documentation locally, run `mkdocs serve` from the project root
- MkDocs supports code highlighting, admonitions, and other Markdown extensions as configured in `mkdocs.yml`

## Documentation Guidelines

### Avoid Marketing Speak and Exaggeration
- Describe functionality accurately without embellishment
- Avoid superlatives like "revolutionary," "groundbreaking," or "best-in-class"
- Focus on what the project does, not how amazing it allegedly is
- Use objective descriptions rather than subjective praise

### Audience Focus
- Write for our intended audience: developers both new and experienced
- Use language and terms familiar to this audience
- Explain technical concepts at appropriate depth

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
- Eliminate unnecessary words and be concise

### Formatting for Readability
- Create short paragraphs (5-7 lines maximum)
- Use lists and bullets for easy scanning
- Separate content into small, digestible chunks
- Use white space generously to improve scan-ability

### Link Text
- Never use "click here" for links
- Link text should describe what users will find at the destination
- Include keywords in link text to help with search engine optimization

## MkDocs Features Used in VMPilot

Use the following MkDocs features to enhance documentation readability:
- code Blocks
- admonitions
- tables
- tabs

## Usage

When a user asks for help with documentation, guide them through:

1. **Determining the purpose**: Help clarify what information needs to be conveyed
2. **Structuring the content**: Suggest appropriate headings and organization
3. **Applying plain language principles**: Edit text to be clear, concise, and active
4. **Ensuring factual accuracy**: Don't use marketing language and exaggerated claims
5. **Enhancing readability**: Format content for easy scanning using MkDocs features

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
