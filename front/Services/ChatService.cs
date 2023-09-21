using Azure;
using System.IO;
using System.Text.Json;
using Azure.AI.OpenAI;
using BlazorCopilot1.Data;

namespace BlazorCopilot1.Services
{
    public class ChatService
    {
        private readonly IConfiguration _configuration;
        private string SystemMessage = "You are an AI assistant that helps people find jobs at Porsche Group. Respond to the User either in English or German depending on the Responses we get from the user.'";

        public ChatService(IConfiguration configuration)
        {
            _configuration = configuration;
        }

        // 1. Model Enhancement
        public class PythonScriptOutput
        {
            public string Response { get; set; }
            public string Context { get; set; }
            public string Language { get; set; }
        }

        // 2. Modify the GetPythonScriptResponse method
       private async Task<PythonScriptOutput> GetPythonScriptOutput()
{
    var resultsPath = "/data/bot_response.json"; // Adjust path if necessary

    if (!File.Exists(resultsPath))
    {
        Console.WriteLine("bot_response.json not found.");
        return new PythonScriptOutput 
        {
            Response = "I processed the file, but no recommendations were found.",
            Context = string.Empty
        };
    }

    var jsonData = await File.ReadAllTextAsync(resultsPath);
    if (string.IsNullOrEmpty(jsonData))
    {
        Console.WriteLine("bot_response.json is empty.");
    }
    var jsonObject = JsonSerializer.Deserialize<PythonScriptOutput>(jsonData);
    Console.WriteLine($"Context from bot_response.json: {jsonObject?.Context ?? "NULL or EMPTY"}");

    
    if (jsonObject == null)
    {
        Console.WriteLine("Deserialization of bot_response.json failed.");
    }

    return jsonObject ?? new PythonScriptOutput();
}
public async Task<Message> GetResponseAfterFileUpload()
{
    var pythonOutput = await GetPythonScriptOutput();

    if (pythonOutput == null || string.IsNullOrEmpty(pythonOutput.Response))
    {
        Console.WriteLine("Python output is null or has an empty response.");
        return new Message("Sorry, I couldn't retrieve recommendations at this time.", false);
    }

    // Mapping of languages to response templates
    Dictionary<string, string> responseTemplates = new Dictionary<string, string>
    {
        { "en", "Thank you for uploading your resume. Here are a few recommendations based on your profile: {0}" },
        { "de", "Vielen Dank für das Hochladen Ihres Lebenslaufs. Hier sind einige Empfehlungen basierend auf Ihrem Profil: {0}" },
    };

    string responseTemplate = responseTemplates.TryGetValue(pythonOutput.Language, out var template) 
        ? template 
        : "{0}";  // Default to just the python response if no match

    string botResponseText = string.Format(responseTemplate, pythonOutput.Response);
    return new Message(botResponseText, false);
}




        // 3. Use the Context in the GetResponse method
        public async Task<Message> GetResponse(List<Message> messagechain)
        {
            string response = "";

            OpenAIClient client = new OpenAIClient(
                new Uri(_configuration.GetSection("Azure")["OpenAIUrl"]!),
                new AzureKeyCredential(_configuration.GetSection("Azure")["OpenAIKey"]!));
            
            ChatCompletionsOptions options = new ChatCompletionsOptions();
            options.Temperature = (float)0.7;
            options.MaxTokens = 800;
            options.NucleusSamplingFactor = (float)0.95;
            options.FrequencyPenalty = 0;
            options.PresencePenalty = 0;
            
            options.Messages.Add(new ChatMessage(ChatRole.System, SystemMessage));

            // Insert the context from bot_response.json
            var pythonOutput = await GetPythonScriptOutput();
            Console.WriteLine($"Using Context for OpenAI: {pythonOutput.Context ?? "NULL or EMPTY"}");

            if (!string.IsNullOrEmpty(pythonOutput.Context))
            {
                options.Messages.Add(new ChatMessage(ChatRole.System, pythonOutput.Context));
            }

            foreach (var msg in messagechain)
            {
                if (msg.IsRequest)
                {
                    options.Messages.Add(new ChatMessage(ChatRole.User, msg.Body));
                }
                else
                {
                    options.Messages.Add(new ChatMessage(ChatRole.Assistant, msg.Body));
                }
            }

            Response<ChatCompletions> resp = await client.GetChatCompletionsAsync(
                _configuration.GetSection("Azure")["OpenAIDeploymentModel"]!,
                options);

            ChatCompletions completions = resp.Value;

            response = completions.Choices[0].Message.Content;

            Message responseMessage = new Message(response, false);
            return responseMessage;
        }        
    }
}
