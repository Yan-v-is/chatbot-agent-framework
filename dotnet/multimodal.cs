using System.ClientModel;
using System.Diagnostics.CodeAnalysis;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using OpenAI.Chat;
using ChatMessage = Microsoft.Extensions.AI.ChatMessage;

public static class Multimodal
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

        AIAgent agent = new AzureOpenAIClient(new Uri(endpoint), new ApiKeyCredential(apiKey))
            .GetChatClient(deploymentName)
            .AsAIAgent(instructions: "You are a helpful agent that can analyze images", name: "VisionAgent");

        ChatMessage message = new(ChatRole.User, [
            new TextContent("What do you see in this image?"),
            new UriContent("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Colombus_Isle.JPG/250px-Colombus_Isle.JPG", "image/jpeg")
        ]);

        Console.WriteLine(await agent.RunAsync(message));
        await Task.CompletedTask;
    }
}