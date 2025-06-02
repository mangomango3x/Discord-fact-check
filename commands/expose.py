import discord
from discord.ext import commands
import logging
from datetime import datetime

from utils.ai_client import AIClient
from utils.fact_checker import FactChecker
from utils.feedback import FeedbackManager
from config import COLORS

logger = logging.getLogger(__name__)

class ExposeCog(commands.Cog):
    """Cog for the expose command that provides facts about statements"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ai_client = AIClient()
        self.fact_checker = FactChecker()
        self.feedback_manager = FeedbackManager()
    
    @commands.command(name='expose', aliases=['fact', 'check'])
    async def expose_command(self, ctx, *, statement: str = None):
        """
        Exposes misinformation by providing factual information about a statement.
        
        Usage: !expose <statement>
        Example: !expose vaccines cause autism
        """
        if not statement:
            embed = discord.Embed(
                title="❌ Missing Statement",
                description="Please provide a statement to fact-check.\n\n**Usage:** `!expose <statement>`\n**Example:** `!expose vaccines cause autism`",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
            return
        
        # Send initial processing message
        processing_msg = await ctx.send("🔍 Analyzing statement and gathering facts...")
        
        try:
            # Get AI analysis
            ai_analysis = await self.ai_client.analyze_statement(statement)
            
            # Get fact-check information from reliable sources
            fact_check_results = await self.fact_checker.check_statement(statement)
            
            # Create response embed
            embed = discord.Embed(
                title="🎯 Statement Analysis",
                description=f"**Statement:** {statement[:500]}{'...' if len(statement) > 500 else ''}",
                color=self.get_embed_color(ai_analysis.get('credibility', 0.5)),
                timestamp=datetime.utcnow()
            )
            
            # Add AI analysis
            if ai_analysis:
                embed.add_field(
                    name="🤖 AI Analysis",
                    value=ai_analysis.get('analysis', 'Unable to analyze statement'),
                    inline=False
                )
                
                # Add credibility score with confidence bar
                credibility = ai_analysis.get('credibility', 0)
                confidence_bar = self.create_confidence_bar(credibility)
                embed.add_field(
                    name="📊 Credibility Score",
                    value=f"{confidence_bar} **{credibility:.1%}**",
                    inline=True
                )
                
                # Add confidence level
                confidence = ai_analysis.get('confidence', 0)
                embed.add_field(
                    name="🎯 AI Confidence",
                    value=f"{confidence:.1%}",
                    inline=True
                )
            
            # Add fact-check sources
            if fact_check_results:
                sources_text = ""
                for source, info in fact_check_results.items():
                    if info.get('relevant'):
                        status_emoji = "✅" if info.get('supports_truth') else "❌"
                        sources_text += f"{status_emoji} **{source.title()}**: {info.get('summary', 'No summary available')}\n\n"
                
                if sources_text:
                    embed.add_field(
                        name="📰 Reliable Sources",
                        value=sources_text[:1000] + ("..." if len(sources_text) > 1000 else ""),
                        inline=False
                    )
            
            # Add factual information
            if ai_analysis and ai_analysis.get('facts'):
                embed.add_field(
                    name="📋 Key Facts",
                    value=ai_analysis['facts'][:800] + ("..." if len(ai_analysis['facts']) > 800 else ""),
                    inline=False
                )
            
            # Add footer
            embed.set_footer(
                text="Use the buttons below to rate this analysis • Data from reliable sources",
                icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
            )
            
            # Create feedback view
            view = self.feedback_manager.create_feedback_view(
                message_id=ctx.message.id,
                user_id=ctx.author.id
            )
            
            # Edit the processing message
            await processing_msg.edit(content=None, embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in expose command: {e}")
            error_embed = discord.Embed(
                title="❌ Analysis Failed",
                description="An error occurred while analyzing the statement. Please try again later.",
                color=COLORS["error"]
            )
            await processing_msg.edit(content=None, embed=error_embed)
    
    def get_embed_color(self, credibility):
        """Get embed color based on credibility score"""
        if credibility >= 0.8:
            return COLORS["success"]
        elif credibility >= 0.6:
            return COLORS["warning"]
        elif credibility >= 0.4:
            return COLORS["neutral"]
        else:
            return COLORS["error"]
    
    def create_confidence_bar(self, value):
        """Create a visual confidence/credibility bar"""
        filled = int(value * 10)
        empty = 10 - filled
        
        if value >= 0.8:
            filled_char = "🟢"
        elif value >= 0.6:
            filled_char = "🟡"
        elif value >= 0.4:
            filled_char = "🟠"
        else:
            filled_char = "🔴"
            
        return filled_char * filled + "⚪" * empty

    @expose_command.error
    async def expose_error(self, ctx, error):
        """Handle errors in expose command"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Statement",
                description="Please provide a statement to fact-check.\n\n**Usage:** `!expose <statement>`",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
        else:
            logger.error(f"Expose command error: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
