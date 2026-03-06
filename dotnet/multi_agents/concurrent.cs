using System.ClientModel;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;

public static class Concurrent
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

        // 2) Helper method to create translation agents
        static ChatClientAgent GetTranslationAgent(string targetLanguage, IChatClient chatClient) =>
            new(chatClient,
                $"Translate everything into {targetLanguage}. Respond only with: <source language>: <translation>.");

        // Create translation agents for concurrent processing
        var translationAgents = (from lang in (string[])["French", "Spanish", "English"]
                                 select GetTranslationAgent(lang, client));

        // 3) Build concurrent workflow
        var workflow = AgentWorkflowBuilder.BuildConcurrent(translationAgents);

        // 4) Run the workflow
        var messages = new List<ChatMessage> { new(ChatRole.User, "Hello, world!") };

        StreamingRun run = await InProcessExecution.RunStreamingAsync(workflow, messages);
        await run.TrySendMessageAsync(new TurnToken(emitEvents: true));

        List<ChatMessage> result = new();
        await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
        {
            if (evt is AgentResponseUpdateEvent e)
            {
                // Console.WriteLine($"{e.ExecutorId}: {e.Data}");
            }
            else if (evt is WorkflowOutputEvent outputEvt)
            {
                result = (List<ChatMessage>)outputEvt.Data!;
                break;
            }
        }

        // Display aggregated results from all agents
        Console.WriteLine("===== Final Aggregated Results =====");
        foreach (var message in result)
        {
            Console.WriteLine($"{message.Role}: {message.Text}");
        }

        await Task.CompletedTask;
    }
}