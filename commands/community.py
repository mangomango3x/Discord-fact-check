
import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from config import COLORS

logger = logging.getLogger(__name__)

class CommunityCog(commands.Cog):
    """Commands for community misinformation tracking and management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='misinfotrends', aliases=['trends', 'patterns'])
    @commands.has_permissions(manage_messages=True)
    async def misinformation_trends(self, ctx):
        """
        Shows misinformation trends and patterns in the community (Moderator only)
        
        Usage: !misinfotrends
        """
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.send("❌ This command is only available in servers.")
                return
            
            # Load community data
            pattern_file = f'data/community_patterns_{guild_id}.json'
            try:
                with open(pattern_file, 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                embed = discord.Embed(
                    title="📊 Community Misinformation Trends",
                    description="No misinformation patterns detected yet in this community.",
                    color=COLORS["success"]
                )
                await ctx.send(embed=embed)
                return
            
            # Analyze trends
            recent_events = [e for e in data.get('events', []) 
                           if datetime.utcnow() - datetime.fromisoformat(e['timestamp']) < timedelta(days=30)]
            
            # Create trends embed
            embed = discord.Embed(
                title="📊 Community Misinformation Trends (Last 30 Days)",
                description=f"Analysis of misinformation patterns in {ctx.guild.name}",
                color=COLORS["info"],
                timestamp=datetime.utcnow()
            )
            
            # Overall stats
            total_alerts = len(recent_events)
            if total_alerts > 0:
                avg_truthiness = sum(e.get('truthiness_score', 50) for e in recent_events) / total_alerts
                high_urgency = len([e for e in recent_events if e.get('urgency') == 'high'])
                
                embed.add_field(
                    name="📈 Overall Statistics",
                    value=(
                        f"**Total Alerts:** {total_alerts}\n"
                        f"**Average Truthiness:** {avg_truthiness:.1f}%\n"
                        f"**High Priority Alerts:** {high_urgency}"
                    ),
                    inline=False
                )
                
                # Top recurring patterns
                claims = data.get('claims', {})
                top_claims = sorted(claims.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
                
                if top_claims:
                    patterns_text = ""
                    for phrase, info in top_claims:
                        patterns_text += f"• **{phrase}** - {info['count']} occurrences\n"
                    
                    embed.add_field(
                        name="🔄 Top Recurring Patterns",
                        value=patterns_text[:1000],
                        inline=False
                    )
                
                # Weekly trend
                weekly_counts = defaultdict(int)
                for event in recent_events:
                    week = datetime.fromisoformat(event['timestamp']).strftime('%Y-W%U')
                    weekly_counts[week] += 1
                
                if len(weekly_counts) > 1:
                    trend_direction = "📈 Increasing" if list(weekly_counts.values())[-1] > list(weekly_counts.values())[0] else "📉 Decreasing"
                    embed.add_field(
                        name="📅 Weekly Trend",
                        value=f"{trend_direction} pattern detected",
                        inline=True
                    )
            
            else:
                embed.add_field(
                    name="✅ Good News!",
                    value="No significant misinformation patterns detected in the last 30 days.",
                    inline=False
                )
            
            embed.set_footer(
                text="Community Protection • Moderator Only",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in misinformation trends command: {e}")
            await ctx.send("❌ An error occurred while analyzing community trends.")
    
    @commands.command(name='communityhealth', aliases=['health'])
    @commands.has_permissions(manage_messages=True)
    async def community_health(self, ctx):
        """
        Shows community health metrics related to misinformation (Moderator only)
        
        Usage: !communityhealth
        """
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.send("❌ This command is only available in servers.")
                return
            
            # Load feedback data
            feedback_file = 'data/feedback.json'
            community_feedback = []
            
            try:
                with open(feedback_file, 'r') as f:
                    all_feedback = json.load(f)
                    community_feedback = [f for f in all_feedback if f.get('guild_id') == str(guild_id)]
            except FileNotFoundError:
                pass
            
            # Create health metrics embed
            embed = discord.Embed(
                title="🏥 Community Health Metrics",
                description=f"Misinformation detection effectiveness in {ctx.guild.name}",
                color=COLORS["info"],
                timestamp=datetime.utcnow()
            )
            
            if community_feedback:
                # Calculate accuracy metrics
                accurate_count = len([f for f in community_feedback if f.get('rating') in ['accurate', 'helpful']])
                false_positive_count = len([f for f in community_feedback if f.get('rating') == 'false_positive'])
                total_feedback = len(community_feedback)
                
                accuracy_rate = (accurate_count / total_feedback * 100) if total_feedback > 0 else 0
                
                # Health score calculation
                health_score = min(100, accuracy_rate + (10 if false_positive_count < total_feedback * 0.1 else 0))
                
                # Color based on health score
                if health_score >= 80:
                    health_color = "🟢 Excellent"
                elif health_score >= 60:
                    health_color = "🟡 Good"
                elif health_score >= 40:
                    health_color = "🟠 Fair"
                else:
                    health_color = "🔴 Needs Improvement"
                
                embed.add_field(
                    name="📊 Detection Accuracy",
                    value=(
                        f"**Health Score:** {health_score:.1f}% {health_color}\n"
                        f"**Accurate Alerts:** {accurate_count}/{total_feedback}\n"
                        f"**False Positives:** {false_positive_count}/{total_feedback}\n"
                        f"**Community Engagement:** {total_feedback} feedback responses"
                    ),
                    inline=False
                )
                
                # Recent performance (last 7 days)
                recent_feedback = [f for f in community_feedback 
                                 if datetime.utcnow() - datetime.fromisoformat(f['timestamp']) < timedelta(days=7)]
                
                if recent_feedback:
                    recent_accurate = len([f for f in recent_feedback if f.get('rating') in ['accurate', 'helpful']])
                    recent_total = len(recent_feedback)
                    recent_accuracy = (recent_accurate / recent_total * 100) if recent_total > 0 else 0
                    
                    embed.add_field(
                        name="📅 Recent Performance (7 days)",
                        value=f"**Accuracy:** {recent_accuracy:.1f}% ({recent_accurate}/{recent_total})",
                        inline=True
                    )
                
                # Recommendations
                recommendations = []
                if false_positive_count > total_feedback * 0.15:
                    recommendations.append("Consider adjusting detection sensitivity")
                if total_feedback < 10:
                    recommendations.append("Encourage more community feedback")
                if health_score < 60:
                    recommendations.append("Review recent alerts for patterns")
                
                if recommendations:
                    embed.add_field(
                        name="💡 Recommendations",
                        value="\n".join(f"• {rec}" for rec in recommendations),
                        inline=False
                    )
            
            else:
                embed.add_field(
                    name="📋 Status",
                    value="No community feedback data available yet. The system is active and monitoring for misinformation.",
                    inline=False
                )
            
            embed.set_footer(
                text="Community Protection System",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in community health command: {e}")
            await ctx.send("❌ An error occurred while analyzing community health.")
    
    @misinformation_trends.error
    @community_health.error
    async def moderator_command_error(self, ctx, error):
        """Handle errors in moderator commands"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Required",
                description="This command requires the **Manage Messages** permission.",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
        else:
            logger.error(f"Moderator command error: {error}")
            await ctx.send("❌ An unexpected error occurred.")
