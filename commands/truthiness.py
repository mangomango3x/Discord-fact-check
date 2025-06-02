import discord
from discord.ext import commands
import logging
from datetime import datetime

from utils.ai_client import AIClient
from utils.feedback import FeedbackManager
from config import COLORS

logger = logging.getLogger(__name__)

class TruthinessCog(commands.Cog):
    """Cog for the truthiness command that rates statement credibility"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ai_client = AIClient()
        self.feedback_manager = FeedbackManager()
    
    @commands.command(name='truthiness', aliases=['truth', 'rate', 'credibility'])
    async def truthiness_command(self, ctx, *, statement: str = None):
        """
        Rates the truthiness/credibility of a statement using AI analysis.
        
        Usage: !truthiness <statement>
        Example: !truthiness the earth is flat
        """
        if not statement:
            embed = discord.Embed(
                title="❌ Missing Statement",
                description="Please provide a statement to rate.\n\n**Usage:** `!truthiness <statement>`\n**Example:** `!truthiness the earth is flat`",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
            return
        
        # Send initial processing message
        processing_msg = await ctx.send("🤔 Analyzing statement truthiness...")
        
        try:
            # Get AI truthiness analysis
            analysis = await self.ai_client.rate_truthiness(statement)
            
            if not analysis:
                raise Exception("No analysis returned from AI")
            
            truthiness_score = analysis.get('truthiness_percentage', 0)
            confidence = analysis.get('confidence', 0)
            reasoning = analysis.get('reasoning', 'No reasoning provided')
            category = analysis.get('category', 'Unknown')
            
            # Create response embed
            embed = discord.Embed(
                title="🎯 Truthiness Rating",
                description=f"**Statement:** {statement[:500]}{'...' if len(statement) > 500 else ''}",
                color=self.get_truthiness_color(truthiness_score),
                timestamp=datetime.utcnow()
            )
            
            # Add main truthiness score
            truthiness_bar = self.create_truthiness_bar(truthiness_score)
            embed.add_field(
                name="📊 Truthiness Score",
                value=f"{truthiness_bar}\n**{truthiness_score:.1f}%** likely to be true",
                inline=False
            )
            
            # Add confidence level
            confidence_bar = self.create_confidence_bar(confidence)
            embed.add_field(
                name="🎯 AI Confidence",
                value=f"{confidence_bar} {confidence:.1%}",
                inline=True
            )
            
            # Add category
            category_emoji = self.get_category_emoji(category)
            embed.add_field(
                name="🏷️ Category",
                value=f"{category_emoji} {category}",
                inline=True
            )
            
            # Add reasoning
            embed.add_field(
                name="🧠 AI Reasoning",
                value=reasoning[:800] + ("..." if len(reasoning) > 800 else ""),
                inline=False
            )
            
            # Add interpretation
            interpretation = self.get_truthiness_interpretation(truthiness_score)
            embed.add_field(
                name="📖 Interpretation",
                value=interpretation,
                inline=False
            )
            
            # Add footer
            embed.set_footer(
                text="Rate this analysis using the buttons below • AI-powered analysis",
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
            logger.error(f"Error in truthiness command: {e}")
            error_embed = discord.Embed(
                title="❌ Analysis Failed",
                description="An error occurred while analyzing the statement. Please try again later.",
                color=COLORS["error"]
            )
            await processing_msg.edit(content=None, embed=error_embed)
    
    def get_truthiness_color(self, score):
        """Get embed color based on truthiness score"""
        if score >= 80:
            return COLORS["success"]  # Green for high truthiness
        elif score >= 60:
            return COLORS["warning"]  # Yellow for moderate
        elif score >= 40:
            return COLORS["neutral"]  # Gray for uncertain
        else:
            return COLORS["error"]  # Red for low truthiness
    
    def create_truthiness_bar(self, score):
        """Create a visual truthiness bar"""
        filled = int(score / 10)
        empty = 10 - filled
        
        if score >= 80:
            filled_char = "🟢"
        elif score >= 60:
            filled_char = "🟡"
        elif score >= 40:
            filled_char = "🟠"
        else:
            filled_char = "🔴"
            
        return filled_char * filled + "⚪" * empty
    
    def create_confidence_bar(self, confidence):
        """Create a visual confidence bar"""
        filled = int(confidence * 10)
        return "█" * filled + "░" * (10 - filled)
    
    def get_category_emoji(self, category):
        """Get emoji for statement category"""
        category_emojis = {
            "Scientific": "🔬",
            "Political": "🏛️",
            "Health": "🏥",
            "Historical": "📚",
            "Technology": "💻",
            "Social": "👥",
            "Economic": "💰",
            "Environmental": "🌍",
            "Unknown": "❓"
        }
        return category_emojis.get(category, "❓")
    
    def get_truthiness_interpretation(self, score):
        """Get interpretation text for truthiness score"""
        if score >= 90:
            return "🟢 **Highly Likely True** - Strong evidence supports this statement"
        elif score >= 80:
            return "🟢 **Likely True** - Good evidence supports this statement"
        elif score >= 70:
            return "🟡 **Probably True** - Some evidence supports this statement"
        elif score >= 60:
            return "🟡 **Uncertain but Leaning True** - Mixed evidence, slightly favors truth"
        elif score >= 50:
            return "🟠 **Uncertain** - Evidence is mixed or insufficient"
        elif score >= 40:
            return "🟠 **Uncertain but Leaning False** - Mixed evidence, slightly favors falsehood"
        elif score >= 30:
            return "🔴 **Probably False** - Some evidence contradicts this statement"
        elif score >= 20:
            return "🔴 **Likely False** - Good evidence contradicts this statement"
        else:
            return "🔴 **Highly Likely False** - Strong evidence contradicts this statement"

    @truthiness_command.error
    async def truthiness_error(self, ctx, error):
        """Handle errors in truthiness command"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Statement",
                description="Please provide a statement to rate.\n\n**Usage:** `!truthiness <statement>`",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
        else:
            logger.error(f"Truthiness command error: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
