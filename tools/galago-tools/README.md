## Tools

Every tool runs a gRPC server that exposes a standard interface; Commands are sent to tools for execution, and correspond to the lowest level idea in the "workflow-protocol-instruction-command" family of concepts. Tool servers are typically written in Python but this is just a convention; there is no reason a given tool server couldn't be written if any other gRPC-supported language.
