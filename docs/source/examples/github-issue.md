# Example: Create GitHub Issue

**Objective:** Use VMPilot to create a new GitHub issue.

## Notes

- We tell the LLM that we want to create a GitHub issue.
- We specifically tell it not to create files or the issue itself, initially. The LLM is "biased" towards action, because its prompt describes the actions it can take, so when we just want to discuss something, we need to be explicit.

![Requesting to create a GitHub issue](github1.png)

![Continuing the conversation](github2.png)

![Continuing the conversation](github3.png)


- Typically, there is more back-and-forth to ensure all details are correct.
- This looks good so we're telling the llm to create the issue.
- This takes a few steps because the LLM needs to:
    - Look at the issue plugin to know how to create an issue.
    - Look at the feature template to know what fields are required.
    - Run the gh command to create the issue.
    - And finally, report back on the success of the operation. [See it on github.](https://github.com/drorm/vmpilot/issues/26).
- Notice that the formatting of the output gets a bit mangled, and the last little bit is fenced when it shouldn't.


![Continuing the conversation](github5.png)
![Continuing the conversation](github6.png)
![Continuing the conversation](github7.png)
