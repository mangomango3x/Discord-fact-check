import discord
from discord.ext import commands
from config import COLORS, COMMAND_PREFIX

class HelpCog(commands.Cog):
    """Cog for help and information commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', aliases=['h', 'commands'])
    async def help_command(self, ctx, command_name=None):
        """
        Shows help information for bot commands.

        Usage: !help [command]
        """
        if command_name:
            await self.show_command_help(ctx, command_name)
        else:
            await self.show_general_help(ctx)

    async def show_general_help(self, ctx):
        """Show general help with all commands"""
        embed = discord.Embed(
            title="🤖 Fact-Check Bot Help",
            description="AI-powered fact-checking and misinformation detection bot",
            color=COLORS["info"]
        )

        # Core Commands
        embed.add_field(
            name="🎯 Core Commands",
            value=(
                f"`{COMMAND_PREFIX}expose <statement>` - Expose misinformation with facts\n"
                f"`{COMMAND_PREFIX}truthiness <statement>` - Rate statement credibility (percentage)\n"
                f"`{COMMAND_PREFIX}help [command]` - Show this help or command details\n"
                f"`{COMMAND_PREFIX}ai` - Show AI model status\n"
                f"`{COMMAND_PREFIX}setmodel <service> <model>` - Change AI models"
            ),
            inline=False
        )

        # Database Commands
        embed.add_field(
            name="🗃️ Database Commands",
            value=(
                f"`{COMMAND_PREFIX}db addfact <claim> | <fact>` - Add fact-check entry\n"
                f"`{COMMAND_PREFIX}db addpattern <pattern>` - Add misinformation pattern\n"
                f"`{COMMAND_PREFIX}db addsource <name> | <url>` - Add trusted source\n"
                f"`{COMMAND_PREFIX}db search <query>` - Search fact entries\n"
                f"`{COMMAND_PREFIX}db` - Show all database commands"
            ),
            inline=False
        )

        # AI Features
        embed.add_field(
            name="🤖 AI Features",
            value=(
                "• **Advanced Analysis** - ChatGPT powered fact-checking\n"
                "• **Credibility Scoring** - Percentage-based truthiness rating\n"
                "• **Context Awareness** - Understands nuanced statements\n"
                "• **Source Integration** - Cross-references reliable fact-checkers"
            ),
            inline=False
        )

        # Interactive Features
        embed.add_field(
            name="⚡ Interactive Features",
            value=(
                "• **Reply Detection** - Mention me in replies to fact-check messages\n"
                "• **Feedback Buttons** - Rate analyses as helpful or not helpful\n"
                "• **Confidence Bars** - Visual confidence indicators\n"
                "• **Rate Limiting** - Prevents spam (5 commands/minute)"
            ),
            inline=False
        )

        # Reliable Sources
        embed.add_field(
            name="📰 Trusted Sources",
            value=(
                "• **Snopes** - Fact-checking and debunking\n"
                "• **FactCheck.org** - Political fact-checking\n"
                "• **PolitiFact** - Political truth rating\n"
                "• **Reuters Fact Check** - News verification\n"
                "• **AP Fact Check** - Associated Press verification"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Use {COMMAND_PREFIX}help <command> for detailed command information",
            icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
        )

        await ctx.send(embed=embed)

    async def show_command_help(self, ctx, command_name):
        """Show detailed help for a specific command"""
        command_name = command_name.lower()

        if command_name in ['expose', 'fact', 'check']:
            embed = discord.Embed(
                title="🎯 Expose Command",
                description="Exposes misinformation by providing factual information",
                color=COLORS["success"]
            )

            embed.add_field(
                name="📝 Usage",
                value=f"`{COMMAND_PREFIX}expose <statement>`",
                inline=False
            )

            embed.add_field(
                name="📋 Aliases",
                value=f"`{COMMAND_PREFIX}fact`, `{COMMAND_PREFIX}check`",
                inline=False
            )

            embed.add_field(
                name="💡 Examples",
                value=(
                    f"`{COMMAND_PREFIX}expose vaccines cause autism`\n"
                    f"`{COMMAND_PREFIX}expose climate change is a hoax`\n"
                    f"`{COMMAND_PREFIX}expose 5G causes COVID-19`"
                ),
                inline=False
            )

            embed.add_field(
                name="🔍 What it does",
                value=(
                    "• Analyzes the statement using AI\n"
                    "• Provides factual counter-information\n"
                    "• Shows credibility score with visual bar\n"
                    "• Cross-references reliable fact-checking sources\n"
                    "• Includes confidence level of the analysis"
                ),
                inline=False
            )

        elif command_name in ['truthiness', 'truth', 'rate', 'credibility']:
            embed = discord.Embed(
                title="📊 Truthiness Command",
                description="Rates the credibility of statements using AI analysis",
                color=COLORS["warning"]
            )

            embed.add_field(
                name="📝 Usage",
                value=f"`{COMMAND_PREFIX}truthiness <statement>`",
                inline=False
            )

            embed.add_field(
                name="📋 Aliases",
                value=f"`{COMMAND_PREFIX}truth`, `{COMMAND_PREFIX}rate`, `{COMMAND_PREFIX}credibility`",
                inline=False
            )

            embed.add_field(
                name="💡 Examples",
                value=(
                    f"`{COMMAND_PREFIX}truthiness the earth is flat`\n"
                    f"`{COMMAND_PREFIX}truthiness coffee is good for health`\n"
                    f"`{COMMAND_PREFIX}truthiness humans never landed on the moon`"
                ),
                inline=False
            )

            embed.add_field(
                name="🔍 What it does",
                value=(
                    "• Provides percentage-based truthiness rating\n"
                    "• Shows visual truthiness bar\n"
                    "• Explains AI reasoning behind the rating\n"
                    "• Categorizes the type of statement\n"
                    "• Includes confidence level and interpretation"
                ),
                inline=False
            )

        else:
            embed = discord.Embed(
                title="❌ Command Not Found",
                description=f"No help available for command: `{command_name}`",
                color=COLORS["error"]
            )

            embed.add_field(
                name="Available Commands",
                value=f"Use `{COMMAND_PREFIX}help` to see all available commands.",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='ai', aliases=['model', 'status'])
    async def ai_status_command(self, ctx):
        """Show current AI model and API status"""
        ai_client = self.bot.ai_client

        embed = discord.Embed(
            title="🤖 AI Model Status",
            description="Current AI configuration and status",
            color=COLORS["info"]
        )

        # Primary AI Service
        if ai_client.pawan_api_key and ai_client.primary_client:
            embed.add_field(
                name="🟢 Primary AI Service",
                value=f"**PawanOsman ChatGPT API**\nModel: `{ai_client.primary_model}`\nStatus: Active",
                inline=False
            )
        else:
            embed.add_field(
                name="🔴 Primary AI Service",
                value="**PawanOsman ChatGPT API**\nStatus: Not configured",
                inline=False
            )

        # Secondary AI Service
        if ai_client.openai_api_key and ai_client.openai_client:
            embed.add_field(
                name="🟡 Secondary AI Service",
                value=f"**OpenAI API**\nModel: `{ai_client.openai_model}`\nStatus: Available as fallback",
                inline=False
            )
        else:
            embed.add_field(
                name="🔴 Secondary AI Service",
                value="**OpenAI API**\nStatus: Not configured",
                inline=False
            )

        # Tertiary AI Service
        if ai_client.gemini_api_key and ai_client.gemini_model:
            embed.add_field(
                name="🟠 Tertiary AI Service",
                value="**Google Gemini API**\nModel: `gemini-1.5-flash`\nStatus: Available as fallback",
                inline=False
            )
        else:
            embed.add_field(
                name="🔴 Tertiary AI Service",
                value="**Google Gemini API**\nStatus: Not configured",
                inline=False
            )

        # Current usage priority
        embed.add_field(
            name="📊 Service Priority",
            value="1️⃣ PawanOsman → 2️⃣ OpenAI → 3️⃣ Gemini",
            inline=False
        )

        embed.add_field(
            name="ℹ️ How it works",
            value="The bot tries each service in order until one responds successfully. If the primary service fails, it automatically falls back to the next available service.",
            inline=False
        )

        embed.set_footer(text="Use !help for more commands")

        await ctx.send(embed=embed)

    @commands.command(name='setmodel', aliases=['changemodel', 'switchmodel'])
    async def set_model_command(self, ctx, service=None, model=None):
        """
        Change AI model for a specific service
        
        Usage: !setmodel <service> <model>
        Services: pawan, openai, gemini
        """
        if not service or not model:
            embed = discord.Embed(
                title="🔧 Model Configuration",
                description="Change AI models for different services",
                color=COLORS["info"]
            )
            
            embed.add_field(
                name="📝 Usage",
                value=f"`{COMMAND_PREFIX}setmodel <service> <model>`",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Available Services",
                value="• `pawan` - PawanOsman ChatGPT API\n• `openai` - OpenAI API\n• `gemini` - Google Gemini API",
                inline=False
            )
            
            embed.add_field(
                name="🤖 Available Models",
                value=(
                    "**Pawan Models:**\n"
                    "• `gpt-3.5-turbo` (default)\n"
                    "• `gpt-4`\n"
                    "• `gpt-4-turbo`\n\n"
                    "**OpenAI Models:**\n"
                    "• `gpt-4o` (default)\n"
                    "• `gpt-4o-mini`\n"
                    "• `gpt-4-turbo`\n"
                    "• `gpt-3.5-turbo`\n\n"
                    "**Gemini Models:**\n"
                    "• `gemini-1.5-flash` (default)\n"
                    "• `gemini-1.5-pro`"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💡 Examples",
                value=(
                    f"`{COMMAND_PREFIX}setmodel pawan gpt-4`\n"
                    f"`{COMMAND_PREFIX}setmodel openai gpt-4o-mini`\n"
                    f"`{COMMAND_PREFIX}setmodel gemini gemini-1.5-pro`"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        service = service.lower()
        ai_client = self.bot.ai_client
        
        success = False
        old_model = None
        
        if service == 'pawan':
            if ai_client.primary_client:
                old_model = ai_client.primary_model
                ai_client.primary_model = model
                success = True
            else:
                await ctx.send("❌ PawanOsman API is not configured. Please check your API key.")
                return
                
        elif service == 'openai':
            if ai_client.openai_client:
                old_model = ai_client.openai_model
                ai_client.openai_model = model
                success = True
            else:
                await ctx.send("❌ OpenAI API is not configured. Please check your API key.")
                return
                
        elif service == 'gemini':
            if ai_client.gemini_model:
                old_model = "gemini-1.5-flash"  # Current default
                # For Gemini, we need to reinitialize with new model
                try:
                    import google.generativeai as genai
                    ai_client.gemini_model = genai.GenerativeModel(model)
                    success = True
                except Exception as e:
                    await ctx.send(f"❌ Failed to set Gemini model: {str(e)}")
                    return
            else:
                await ctx.send("❌ Gemini API is not configured. Please check your API key.")
                return
        else:
            await ctx.send("❌ Invalid service. Use: `pawan`, `openai`, or `gemini`")
            return
        
        if success:
            embed = discord.Embed(
                title="✅ Model Updated Successfully",
                color=COLORS["success"]
            )
            
            embed.add_field(
                name="Service",
                value=service.title(),
                inline=True
            )
            
            embed.add_field(
                name="Previous Model",
                value=f"`{old_model}`",
                inline=True
            )
            
            embed.add_field(
                name="New Model",
                value=f"`{model}`",
                inline=True
            )
            
            embed.add_field(
                name="ℹ️ Note",
                value="The new model will be used for all future AI requests to this service.",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to update model. Please try again.")

    @commands.command(name='about', aliases=['info'])
    async def about_command(self, ctx):
        """Show information about the bot"""
        embed = discord.Embed(
            title="🤖 About Fact-Check Bot",
            description="An AI-powered Discord bot designed to combat misinformation",
            color=COLORS["info"]
        )

        embed.add_field(
            name="🎯 Purpose",
            value=(
                "This bot helps users identify and understand misinformation by providing "
                "fact-based analysis and credibility ratings using advanced AI technology."
            ),
            inline=False
        )

        embed.add_field(
            name="🧠 AI Technology",
            value=(
                "• **GPT-4o** - Latest OpenAI model for analysis\n"
                "• **Advanced Reasoning** - Context-aware fact-checking\n"
                "• **Multi-source Verification** - Cross-references multiple sources"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Features",
            value=(
                "• Real-time fact-checking\n"
                "• Percentage-based truthiness ratings\n"
                "• Interactive feedback system\n"
                "• Reply-based fact-checking\n"
                "• Rate limiting for fair usage"
            ),
            inline=False
        )

        embed.add_field(
            name="🔒 Privacy & Security",
            value=(
                "• No personal data stored\n"
                "• Feedback data is anonymized\n"
                "• Rate limiting prevents abuse\n"
                "• Open source methodology"
            ),
            inline=False
        )

        embed.set_footer(
            text="Use !help to see available commands",
            icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
        )

        await ctx.send(embed=embed)

    @commands.command(name='help2', aliases=['h2', 'commands2'])
    async def help2_command(self, ctx, command_name=None):
        """
        Alternative help command - shows help information for bot commands.

        Usage: !help2 [command]
        """
        if command_name:
            await self.show_command_help(ctx, command_name)
        else:
            await self.show_general_help(ctx)

    @help_command.error
    @help2_command.error
    async def help_error(self, ctx, error):
        """Handle help command errors"""
        await ctx.send("❌ An error occurred while showing help. Please try again.")