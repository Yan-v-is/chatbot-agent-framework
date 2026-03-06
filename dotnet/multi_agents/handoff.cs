using System.ClientModel;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;

public static class Handoff
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

        // 2) Create specialized agents
        ChatClientAgent historyTutor = new(client,
            "You provide assistance with historical queries. Explain important events and context clearly. Only respond about history.",
            "history_tutor",
            "Specialist agent for historical questions");

        ChatClientAgent mathTutor = new(client,
            "You provide help with math problems. Explain your reasoning including examples. Only respond about math.",
            "math_tutor",
            "Specialist agent for math questions");

        ChatClientAgent triageAgent = new(client,
            "You determine which agent to use based on the user's question. ALWAYS handoff to another agent.",
            "triage_agent",
            "Routes messages to the appropriate specialist agent");

        List<ChatMessage> messages = new();

        while (true)
        {
            Console.Write("Q: ");
            string userInput = Console.ReadLine()!;
            messages.Add(new(ChatRole.User, userInput));

            var workflow = AgentWorkflowBuilder.CreateHandoffBuilderWith(triageAgent)
                .WithHandoffs(triageAgent, [mathTutor, historyTutor]) // Triage can route to either specialist
                .WithHandoff(mathTutor, triageAgent)                  // Math tutor can return to triage
                .WithHandoff(historyTutor, triageAgent)               // History tutor can return to triage
                .Build();


            // Execute workflow and process events
            StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, messages);
            await run.TrySendMessageAsync(new TurnToken(emitEvents: true));

            List<ChatMessage> newMessages = new();
            await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
            {
                if (evt is AgentResponseUpdateEvent e)
                {
                    Console.WriteLine($"{e.ExecutorId}: {e.Data}");
                }
                else if (evt is WorkflowOutputEvent outputEvt)
                {
                    newMessages = (List<ChatMessage>)outputEvt.Data!;
                    foreach (var message in newMessages)
                    {
                        Console.WriteLine($"{message.Role}: {message.Text}");
                    }

                    break;
                }
            }

            // Add new messages to conversation history
            // messages.AddRange(newMessages.Skip(messages.Count));

            // Clear messages to not keep history
            messages.Clear();
        }
    }
}