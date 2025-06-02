
import discord
from discord.ext import commands
import logging
from datetime import datetime
import json

from config import COLORS, COMMAND_PREFIX
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

class DatabaseCog(commands.Cog):
    """Commands for managing fact-checking database"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
    
    @commands.group(name='db', aliases=['database'], invoke_without_command=True)
    async def database_group(self, ctx):
        """
        Database management commands
        
        Usage: !db <subcommand>
        """
        if not self.db.enabled:
            embed = discord.Embed(
                title="❌ Database Not Available",
                description="PostgreSQL database is not configured. Please set up DATABASE_URL environment variable.",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🗃️ Database Management",
            description="Available database commands:",
            color=COLORS["info"]
        )
        
        embed.add_field(
            name="📝 Data Entry Commands",
            value=(
                f"`{COMMAND_PREFIX}db addfact <claim> | <fact_check> | [sources] | [score] | [category] | [tags]`\n"
                f"`{COMMAND_PREFIX}db addpattern <pattern> | [description] | [severity]`\n"
                f"`{COMMAND_PREFIX}db addsource <name> | <url> | [description] | [score] | [category]`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔍 Search Commands",
            value=(
                f"`{COMMAND_PREFIX}db search <query>` - Search fact entries\n"
                f"`{COMMAND_PREFIX}db patterns` - View misinformation patterns\n"
                f"`{COMMAND_PREFIX}db sources` - View trusted sources"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Info Commands",
            value=(
                f"`{COMMAND_PREFIX}db stats` - Database statistics\n"
                f"`{COMMAND_PREFIX}db help` - This help message"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @database_group.command(name='addfact', aliases=['addentry', 'fact'])
    async def add_fact_entry(self, ctx, *, content):
        """
        Add a fact-check entry to the database
        
        Usage: !db addfact <claim> | <fact_check> | [sources] | [truthiness_score] | [category] | [tags]
        
        Example: !db addfact The Earth is flat | The Earth is an oblate spheroid | NASA, Wikipedia | 5 | Science | flat-earth, conspiracy
        """
        if not self.db.enabled:
            await ctx.send("❌ Database not available.")
            return
        
        try:
            # Parse the input
            parts = [part.strip() for part in content.split('|')]
            
            if len(parts) < 2:
                embed = discord.Embed(
                    title="❌ Invalid Format",
                    description=(
                        "Please use the format:\n"
                        f"`{COMMAND_PREFIX}db addfact <claim> | <fact_check> | [sources] | [score] | [category] | [tags]`\n\n"
                        "**Required:**\n"
                        "• Claim: The statement to fact-check\n"
                        "• Fact check: The factual response\n\n"
                        "**Optional:**\n"
                        "• Sources: Comma-separated list\n"
                        "• Score: Truthiness score (0-100)\n"
                        "• Category: Topic category\n"
                        "• Tags: Comma-separated tags"
                    ),
                    color=COLORS["error"]
                )
                await ctx.send(embed=embed)
                return
            
            claim = parts[0]
            fact_check = parts[1]
            sources = parts[2] if len(parts) > 2 and parts[2] else None
            
            # Parse truthiness score
            truthiness_score = None
            if len(parts) > 3 and parts[3]:
                try:
                    truthiness_score = int(parts[3])
                    if not 0 <= truthiness_score <= 100:
                        raise ValueError("Score must be between 0-100")
                except ValueError:
                    await ctx.send("❌ Truthiness score must be a number between 0-100")
                    return
            
            category = parts[4] if len(parts) > 4 and parts[4] else None
            tags = parts[5] if len(parts) > 5 and parts[5] else None
            
            # Add to database
            entry_id = self.db.add_fact_entry(
                claim=claim,
                fact_check=fact_check,
                sources=sources,
                truthiness_score=truthiness_score,
                category=category,
                tags=tags,
                user_id=ctx.author.id,
                guild_id=ctx.guild.id if ctx.guild else None
            )
            
            if entry_id:
                embed = discord.Embed(
                    title="✅ Fact Entry Added",
                    description=f"Successfully added fact entry #{entry_id}",
                    color=COLORS["success"],
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(name="📝 Claim", value=claim[:1000], inline=False)
                embed.add_field(name="✅ Fact Check", value=fact_check[:1000], inline=False)
                
                if sources:
                    embed.add_field(name="📚 Sources", value=sources[:500], inline=True)
                if truthiness_score is not None:
                    embed.add_field(name="📊 Score", value=f"{truthiness_score}%", inline=True)
                if category:
                    embed.add_field(name="📂 Category", value=category, inline=True)
                if tags:
                    embed.add_field(name="🏷️ Tags", value=tags, inline=True)
                
                embed.set_footer(text=f"Added by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to add fact entry to database.")
                
        except Exception as e:
            logger.error(f"Error adding fact entry: {e}")
            await ctx.send("❌ An error occurred while adding the fact entry.")
    
    @database_group.command(name='addpattern', aliases=['pattern'])
    async def add_misinformation_pattern(self, ctx, *, content):
        """
        Add a misinformation pattern to track
        
        Usage: !db addpattern <pattern> | [description] | [severity]
        
        Example: !db addpattern vaccines cause autism | Debunked claim linking vaccines to autism | high
        """
        if not self.db.enabled:
            await ctx.send("❌ Database not available.")
            return
        
        try:
            parts = [part.strip() for part in content.split('|')]
            
            if len(parts) < 1:
                await ctx.send(f"❌ Usage: `{COMMAND_PREFIX}db addpattern <pattern> | [description] | [severity]`")
                return
            
            pattern_text = parts[0]
            description = parts[1] if len(parts) > 1 and parts[1] else None
            severity = parts[2] if len(parts) > 2 and parts[2] else 'medium'
            
            # Validate severity
            valid_severities = ['low', 'medium', 'high', 'critical']
            if severity not in valid_severities:
                await ctx.send(f"❌ Severity must be one of: {', '.join(valid_severities)}")
                return
            
            pattern_id = self.db.add_misinformation_pattern(
                pattern_text=pattern_text,
                description=description,
                severity=severity,
                user_id=ctx.author.id,
                guild_id=ctx.guild.id if ctx.guild else None
            )
            
            if pattern_id:
                embed = discord.Embed(
                    title="✅ Misinformation Pattern Added",
                    description=f"Successfully added pattern #{pattern_id}",
                    color=COLORS["success"],
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(name="🔍 Pattern", value=pattern_text, inline=False)
                if description:
                    embed.add_field(name="📝 Description", value=description, inline=False)
                
                severity_emojis = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
                embed.add_field(name="⚠️ Severity", value=f"{severity_emojis[severity]} {severity.title()}", inline=True)
                
                embed.set_footer(text=f"Added by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to add misinformation pattern.")
                
        except Exception as e:
            logger.error(f"Error adding misinformation pattern: {e}")
            await ctx.send("❌ An error occurred while adding the pattern.")
    
    @database_group.command(name='addsource', aliases=['source'])
    async def add_trusted_source(self, ctx, *, content):
        """
        Add a trusted source to the database
        
        Usage: !db addsource <name> | <url> | [description] | [credibility_score] | [category]
        
        Example: !db addsource Snopes | https://snopes.com | Fact-checking website | 95 | Fact-checking
        """
        if not self.db.enabled:
            await ctx.send("❌ Database not available.")
            return
        
        try:
            parts = [part.strip() for part in content.split('|')]
            
            if len(parts) < 2:
                embed = discord.Embed(
                    title="❌ Invalid Format",
                    description=(
                        "Please use the format:\n"
                        f"`{COMMAND_PREFIX}db addsource <name> | <url> | [description] | [score] | [category]`\n\n"
                        "**Required:**\n"
                        "• Name: Source name\n"
                        "• URL: Source website\n\n"
                        "**Optional:**\n"
                        "• Description: Brief description\n"
                        "• Score: Credibility score (0-100, default 90)\n"
                        "• Category: Source category"
                    ),
                    color=COLORS["error"]
                )
                await ctx.send(embed=embed)
                return
            
            name = parts[0]
            url = parts[1]
            description = parts[2] if len(parts) > 2 and parts[2] else None
            
            # Parse credibility score
            credibility_score = 90  # default
            if len(parts) > 3 and parts[3]:
                try:
                    credibility_score = int(parts[3])
                    if not 0 <= credibility_score <= 100:
                        raise ValueError("Score must be between 0-100")
                except ValueError:
                    await ctx.send("❌ Credibility score must be a number between 0-100")
                    return
            
            category = parts[4] if len(parts) > 4 and parts[4] else None
            
            source_id = self.db.add_trusted_source(
                name=name,
                url=url,
                description=description,
                credibility_score=credibility_score,
                category=category,
                user_id=ctx.author.id,
                guild_id=ctx.guild.id if ctx.guild else None
            )
            
            if source_id:
                embed = discord.Embed(
                    title="✅ Trusted Source Added",
                    description=f"Successfully added source #{source_id}",
                    color=COLORS["success"],
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(name="📰 Name", value=name, inline=True)
                embed.add_field(name="🔗 URL", value=url, inline=True)
                embed.add_field(name="📊 Credibility", value=f"{credibility_score}%", inline=True)
                
                if description:
                    embed.add_field(name="📝 Description", value=description, inline=False)
                if category:
                    embed.add_field(name="📂 Category", value=category, inline=True)
                
                embed.set_footer(text=f"Added by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to add trusted source.")
                
        except Exception as e:
            logger.error(f"Error adding trusted source: {e}")
            await ctx.send("❌ An error occurred while adding the source.")
    
    @database_group.command(name='search', aliases=['find'])
    async def search_database(self, ctx, *, query):
        """
        Search fact entries in the database
        
        Usage: !db search <query>
        """
        if not self.db.enabled:
            await ctx.send("❌ Database not available.")
            return
        
        try:
            results = self.db.search_fact_entries(
                query=query,
                guild_id=ctx.guild.id if ctx.guild else None,
                limit=5
            )
            
            if not results:
                embed = discord.Embed(
                    title="🔍 Search Results",
                    description=f"No fact entries found matching '{query}'",
                    color=COLORS["neutral"]
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🔍 Search Results",
                description=f"Found {len(results)} fact entries matching '{query}'",
                color=COLORS["info"]
            )
            
            for i, result in enumerate(results[:3], 1):
                claim = result['claim'][:200] + ("..." if len(result['claim']) > 200 else "")
                fact_check = result['fact_check'][:300] + ("..." if len(result['fact_check']) > 300 else "")
                
                field_value = f"**Claim:** {claim}\n**Fact Check:** {fact_check}"
                
                if result['truthiness_score']:
                    field_value += f"\n**Score:** {result['truthiness_score']}%"
                if result['category']:
                    field_value += f"\n**Category:** {result['category']}"
                
                embed.add_field(
                    name=f"📝 Entry #{result['id']}",
                    value=field_value,
                    inline=False
                )
            
            if len(results) > 3:
                embed.set_footer(text=f"Showing 3 of {len(results)} results")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error searching database: {e}")
            await ctx.send("❌ An error occurred while searching the database.")
    
    @database_group.command(name='patterns')
    async def view_patterns(self, ctx):
        """
        View misinformation patterns
        
        Usage: !db patterns
        """
        if not self.db.enabled:
            await ctx.send("❌ Database not available.")
            return
        
        try:
            patterns = self.db.get_misinformation_patterns(
                guild_id=ctx.guild.id if ctx.guild else None,
                limit=10
            )
            
            if not patterns:
                embed = discord.Embed(
                    title="🔍 Misinformation Patterns",
                    description="No misinformation patterns found for this community.",
                    color=COLORS["neutral"]
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🔍 Misinformation Patterns",
                description=f"Found {len(patterns)} patterns in this community",
                color=COLORS["warning"]
            )
            
            severity_emojis = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
            
            for pattern in patterns[:5]:
                severity_emoji = severity_emojis.get(pattern['severity'], '🟡')
                field_value = f"**Pattern:** {pattern['pattern_text']}\n"
                field_value += f"**Frequency:** {pattern['frequency']} times\n"
                field_value += f"**Severity:** {severity_emoji} {pattern['severity'].title()}\n"
                field_value += f"**Last Seen:** {pattern['last_seen'].strftime('%Y-%m-%d %H:%M')}"
                
                if pattern['description']:
                    field_value += f"\n**Description:** {pattern['description'][:100]}"
                
                embed.add_field(
                    name=f"⚠️ Pattern #{pattern['id']}",
                    value=field_value,
                    inline=False
                )
            
            if len(patterns) > 5:
                embed.set_footer(text=f"Showing 5 of {len(patterns)} patterns")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error viewing patterns: {e}")
            await ctx.send("❌ An error occurred while retrieving patterns.")
