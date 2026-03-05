using System.ClientModel;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Extensions.Configuration;
using OpenAI.Chat;

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
    .AsAIAgent(instructions: "You are a friendly assistant. Keep your answers brief.", name: "HelloAgent");

Console.WriteLine(await agent.RunAsync("What is the largest city in France?"));