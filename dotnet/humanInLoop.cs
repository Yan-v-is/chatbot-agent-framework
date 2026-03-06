using System;
using System.ClientModel;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.Configuration;
using OpenAI.Chat;

public static class HumanInLoop
{
    public async static Task Run()
    {
        var numberRequestPort = RequestPort.Create<NumberSignal, int>("GuessNumber");
        
        JudgeExecutor judgeExecutor = new(42);
        var workflow = new WorkflowBuilder(numberRequestPort)
            .AddEdge(numberRequestPort, judgeExecutor)
            .AddEdge(judgeExecutor, numberRequestPort)
            .WithOutputFrom(judgeExecutor)
            .Build();

        await using StreamingRun handle = await InProcessExecution.RunStreamingAsync(workflow, NumberSignal.Init);
        await foreach (WorkflowEvent evt in handle.WatchStreamAsync())
        {
            Console.WriteLine($"[DEBUG] Event: {evt.GetType().Name}");
            switch (evt)
            {
                case RequestInfoEvent requestInputEvt:
                    Console.WriteLine($"[DEBUG] RequestId: {requestInputEvt.Request.RequestId}");
                    int guess;
                    while (true)
                    {
                        Console.Write("Saisis un nombre : ");
                        var input = Console.ReadLine();
                        if (int.TryParse(input, out guess))
                            break;

                        Console.WriteLine("⚠️ Entier invalide, réessaie.");
                    }
                    await handle.SendResponseAsync(requestInputEvt.Request.CreateResponse(guess));
                    Console.WriteLine($"[DEBUG] Response sent for RequestId: {requestInputEvt.Request.RequestId}");
                    break;

                case WorkflowOutputEvent outputEvt:
                    // The workflow has yielded output
                    Console.WriteLine($"Workflow completed with result: {outputEvt.Data}");
                    return;
                case WorkflowErrorEvent err:
                    Console.WriteLine($"❌ Workflow error: {err.Exception}");
                    // Optionnel: err.Exception?.StackTrace
                    return;

                default:
                    Console.WriteLine("coucou");
                    break;
            }
        }

        await Task.CompletedTask;
    }


}

internal enum NumberSignal
{
    Init,
    Above,
    Below,
}

internal sealed class JudgeExecutor() : Executor<int>("Judge")
{
    private readonly int _targetNumber;
    private int _tries;
    public JudgeExecutor(int targetNumber) : this()
    {
        this._targetNumber = targetNumber;
    }

    public override async ValueTask HandleAsync(int message, IWorkflowContext context, CancellationToken cancellationToken = default)
    {
        this._tries++;
        if (message == this._targetNumber)
        {
            await context.YieldOutputAsync($"{this._targetNumber} found in {this._tries} tries!", cancellationToken);
        }
        else if (message < this._targetNumber)
        {
            await context.SendMessageAsync(NumberSignal.Below, cancellationToken: cancellationToken);
        }
        else
        {
            await context.SendMessageAsync(NumberSignal.Above, cancellationToken: cancellationToken);
        }
    }
}
