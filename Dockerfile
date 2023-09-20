# syntax=docker/dockerfile:1

# Use the SDK image for building the app
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build-env
WORKDIR /front

# Copy csproj and restore dependencies
COPY front/*.csproj ./
RUN dotnet restore

# Copy the rest of the source files
COPY front/ ./
RUN dotnet publish -c Release -o /publish

# Use the ASP.NET runtime image
FROM mcr.microsoft.com/dotnet/aspnet:7.0 AS runtime
WORKDIR /publish
RUN mkdir -p /data/uploaded_files

# Copy the published app from the build-env
COPY --from=build-env /publish .

# Expose port 80 for the app
EXPOSE 80

ENTRYPOINT ["dotnet", "BlazorCopilot1.dll"]
