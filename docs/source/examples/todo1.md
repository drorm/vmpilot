# Example: Create GitHub Issue

**Objective:** Initial implementation of issue 26: Create a python todo list.

## Notes

- In the previous example, we created [github issue 26](https://github.com/drorm/vmpilot/issues/26): Create a python todo app.
- Now we can simply refer to that issue in the conversation, and collaborate with the LLM to implement it.
- Again we specifically tell the LLM to discuss the issue, not to create files or the issue itself, initially.

![Requesting to implement the issue](todo1.png)

![Continuing the conversation](todo2.png)

![Continuing the conversation](todo3.png)

- It started above by looking at the issue and some files, and suggests a comprehensive plan to implement the issue.
- The plan looks good overall, but needs refining to save the data to a JSON file. 
- The LLM starts to implement the plan.

- And I ask it to run the app to test it.

![Continuing the conversation](todo4.png)

![Continuing the conversation](todo5.png)

- The testing looks good, but I noticed that the JSON file is in the root of the project, and I wanted it in the same directory as the app. So I ask the LLM to fix that and review the README.

![Continuing the conversation](todo6.png)

![Continuing the conversation](todo7.png)

![Continuing the conversation](todo8.png)

![Continuing the conversation](todo9.png)
