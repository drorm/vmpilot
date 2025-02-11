# Plugins

Plugins are a way to extend the functionality of the llm. They are different from conventional plugins in that they are just text.


# How they work.

The app injects the plugin's README.md into the llm's prompt. As of this wriitng, this is what it looks like:
```markdown

# Available plugins

# Codemap
directory: codemap
Creates documentation by scanning the code and generating a doc per source file.

# Github

directory: github\_issues
- To view or list issues, use "cd $rootDir && gh issue view $number" or "gh issue list". Always include the "gh" command.
- To create an issue view the README.md file for instructions.
```

# Enabling and disabling Plugins

To enable, disable a plugin simply add or remove the entry from the README.md file. 

# Creating a plugin

To create a plugin,
- Create a directory in the plugins directory. 
- Add a README.md file using the template.md in the plugins directory.
- Add the plugin to the README.md file in the plugins directory.


