using System.ClientModel;
using System.ComponentModel;
using Azure.AI.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using OpenAI.Chat;

public static class Step2 {
    public async static Task Run(){
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
            .AsAIAgent(instructions: "You are a friendly assistant. Keep your answers brief.", name: "HelloAgent",
                tools: [AIFunctionFactory.Create(GetWeather)]);

        Console.WriteLine(await agent.RunAsync("What is the weather like in Amsterdam?"));

        await Task.CompletedTask;
    }

    [Description("Get the weather for a given location.")]
    public static string GetWeather([Description("The location to get the weather for.")] string location) 
        => $"The weather in {location} is cloudy with a high of 15°C.";
}