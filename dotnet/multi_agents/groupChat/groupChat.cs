using System.ClientModel;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;

public static class GroupChat
{
    public async static Task Run()
    {
        var builder = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true);

        IConfiguration config = builder.Build();

        var endpoint = config["AZURE_OPENAI_ENDPOINT"]
            ?? throw new InvalidOperationException("Set AZURE_OPENAI_ENDPOINT");
        var deploymentName = config["AZURE_OPENAI_DEPLOYMENT_NAME"]
            ?? throw new InvalidOperationException("Set AZURE_OPENAI_DEPLOYMENT_NAME");
        string apiKey = config["AZURE_OPENAI_API_KEY"]
            ?? throw new InvalidOperationException("Set AZURE_OPENAI_API_KEY");


        var client = new AzureOpenAIClient(new Uri(endpoint), new ApiKeyCredential(apiKey))
            .GetChatClient(deploymentName)
            .AsIChatClient();

        // Create a copywriter agent
        ChatClientAgent writer = new(client,
            "You are a creative copywriter. Generate catchy slogans and marketing copy. Be concise and impactful.",
            "CopyWriter",
            "A creative copywriter agent");

        // Create a reviewer agent
        ChatClientAgent reviewer = new(client,
            "You are a marketing reviewer. Evaluate slogans for clarity, impact, and brand alignment. " +
            "Provide constructive feedback or approval.",
            "Reviewer",
            "A marketing review agent");

        // Build group chat with round-robin speaker selection
        // The manager factory receives the list of agents and returns a configured manager
        // var workflow = AgentWorkflowBuilder
        //     .CreateGroupChatBuilderWith(agents =>
        //         new RoundRobinGroupChatManager(agents)
        //         {
        //             MaximumIterationCount = 5  // Maximum number of turns
        //         })
        //     .AddParticipants(writer, reviewer)
        //     .Build();

        // Use custom manager in workflow
        var workflow = AgentWorkflowBuilder
            .CreateGroupChatBuilderWith(agents =>
                new ApprovalBasedManager(agents, "Reviewer")
                {
                    MaximumIterationCount = 10
                })
            .AddParticipants(writer, reviewer)
            .Build();

        // Start the group chat
        var messages = new List<ChatMessage> {
            new(ChatRole.User, "Create a slogan for an eco-friendly electric vehicle.")
        };

        StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, messages);
        await run.TrySendMessageAsync(new TurnToken(emitEvents: true));

        await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
        {
            if (evt is AgentResponseUpdateEvent update)
            {
                // Process streaming agent responses
                AgentResponse response = update.AsResponse();
                foreach (ChatMessage message in response.Messages)
                {
                    Console.WriteLine($"[{update.ExecutorId}]: {message.Text}");
                }
            }
            else if (evt is WorkflowOutputEvent output)
            {
                // Workflow completed
                var conversationHistory = output.As<List<ChatMessage>>();
                Console.WriteLine("\n=== Final Conversation ===");
                foreach (var message in conversationHistory)
                {
                    Console.WriteLine($"{message.AuthorName}: {message.Text}");
                }
                break;
            }
        }

        await Task.CompletedTask;
    }
}