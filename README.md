# Chainlit SmolAgents

This project utilizes [Chainlit](https://github.com/Chainlit/chainlit) with a custom datalayer and OAuth authentication for secure, persistent chat history and user data management. It also integrates Gemini and supports models from the GitHub marketplace.

## Prerequisites

- [Chainlit Datalayer](https://github.com/Chainlit/chainlit-datalayer) for chat history and user data storage
- [Chainlit OAuth Authentication](https://docs.chainlit.io/authentication/oauth)
- Python 3.11 or higher

## Synchronous and Asynchronous Code Handling

The application uses the following Chainlit utilities to manage async/sync operations:

- `cl.run_sync()`: Used to run asynchronous code in synchronous contexts, particularly in agent callbacks
- `cl.make_async()`: Used to convert synchronous functions (like the agent's `run()` method) into asynchronous functions

These utilities are implemented in the `on_message` event handler where:
1. Synchronous callbacks are executed with `cl.run_sync(step.update())`
2. The synchronous agent.run method is converted with `await cl.make_async(agent.run)()`

## Environment Variables

Set the following environment variables using a `.env` file or with `chainlit create secret`:

```
GITHUB_API_KEY=
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
CHAINLIT_AUTH_SECRET=
GEMINI_API_KEY=
```

## Installation

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2. Run the application:
    ```bash
    chainlit run app.py -w
    ```

## Additional Notes

- Ensure the datalayer is properly configured and running.
- For authentication, follow the [Chainlit OAuth documentation](https://docs.chainlit.io/authentication/oauth).
- Gemini and GitHub marketplace models are supported and tested.

---