using System.ClientModel;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Extensions.Configuration;
using OpenAI.Chat;

public static class StructuredOutput
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
            .AsAIAgent(instructions: "You are a friendly assistant. Keep your answers brief.", name: "ConversationAgent");

        AgentResponse<PersonInfo> response = await agent.RunAsync<PersonInfo>("Please provide information about John Smith, who is a 35-year-old software engineer.");

        Console.WriteLine($"Name: {response.Result.Name}, Age: {response.Result.Age}, Occupation: {response.Result.Occupation}");
    }

    public class PersonInfo
    {
        public string? Name { get; set; }
        public int? Age {get; set;}
        public string? Occupation { get; set; }
    }
}