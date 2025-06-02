import asyncio
import discord
from discord.ext import commands
import json
import os
import logging
from datetime import datetime, timedelta
from aiohttp import web
import threading

from config import (BOT_TOKEN, COMMAND_PREFIX, AUTO_DETECT_ENABLED, 
                    AUTO_DETECT_TRUTHINESS_THRESHOLD, AUTO_DETECT_CONFIDENCE_THRESHOLD,
                    AUTO_DETECT_MIN_MESSAGE_LENGTH, AUTO_DETECT_RATE_LIMIT)
from commands.expose import ExposeCog
from commands.truthiness import TruthinessCog
from commands.help import HelpCog
from utils.feedback import FeedbackManager
from utils.ai_client import AIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

class FactCheckBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            help_command=None  # We'll use custom help
        )
        self.feedback_manager = FeedbackManager()
        self.ai_client = AIClient()
        self.rate_limits = {}
        self.start_health_server()
        
    async def setup_hook(self):
        """Setup hook called when bot is starting up"""
        # Add cogs
        await self.add_cog(ExposeCog(self))
        await self.add_cog(TruthinessCog(self))
        await self.add_cog(HelpCog(self))
        
        # Import and add community cog
        from commands.community import CommunityCog
        await self.add_cog(CommunityCog(self))
        
        # Import and add database cog
        from commands.database import DatabaseCog
        await self.add_cog(DatabaseCog(self))
        
        # Load rate limit data
        self.load_rate_limits()
        
        logger.info("Bot setup complete")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for misinformation | !help"
            )
        )
    
    async def on_message(self, message):
        """Handle incoming messages"""
        if message.author == self.user:
            return
        
        # Check if bot was mentioned for fact-checking a replied message
        if self.user in message.mentions and message.reference:
            logger.info(f"Bot mentioned in reply by {message.author} - processing fact-check")
            # Check rate limiting for mentions
            if not self.check_rate_limit(message.author.id):
                await message.channel.send(
                    "⏱️ You're sending requests too quickly. Please wait a moment before trying again."
                )
                return
            await self.handle_reply_fact_check(message)
            return
            
        # Check for commands (messages starting with prefix)
        if message.content.startswith(COMMAND_PREFIX):
            # Check rate limiting for commands
            if not self.check_rate_limit(message.author.id):
                await message.channel.send(
                    "⏱️ You're sending commands too quickly. Please wait a moment before trying again."
                )
                return
            
            # Process commands
            await self.process_commands(message)
            return
        
        # Automatic misinformation detection for all messages
        if AUTO_DETECT_ENABLED and message.content and len(message.content.strip()) > AUTO_DETECT_MIN_MESSAGE_LENGTH:
            await self.handle_automatic_misinformation_check(message)
    
    async def handle_reply_fact_check(self, message):
        """Handle fact-checking when bot is mentioned in a reply"""
        try:
            # Get the original message being replied to
            original_message = await message.channel.fetch_message(message.reference.message_id)
            
            if original_message.content:
                # Create an embed for the fact-check
                embed = discord.Embed(
                    title="🔍 Fact-Check Analysis",
                    description=f"Analyzing statement from {original_message.author.mention}",
                    color=0x3498db,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Original Statement",
                    value=original_message.content[:1000] + ("..." if len(original_message.content) > 1000 else ""),
                    inline=False
                )
                
                # Get AI analysis
                analysis = await self.ai_client.analyze_statement(original_message.content)
                
                if analysis:
                    embed.add_field(
                        name="AI Analysis",
                        value=analysis.get('analysis', 'Unable to analyze'),
                        inline=False
                    )
                    
                    confidence = analysis.get('confidence', 0)
                    confidence_bar = self.create_confidence_bar(confidence)
                    embed.add_field(
                        name="Confidence Level",
                        value=f"{confidence_bar} {confidence:.1%}",
                        inline=False
                    )
                
                # Send with feedback buttons
                view = self.feedback_manager.create_feedback_view(
                    message_id=original_message.id,
                    user_id=message.author.id
                )
                
                await message.channel.send(embed=embed, view=view)
                
        except Exception as e:
            logger.error(f"Error handling reply fact-check: {e}")
            await message.channel.send(
                "❌ An error occurred while fact-checking the message."
            )
    
    async def handle_automatic_misinformation_check(self, message):
        """Enhanced automatic misinformation detection with context awareness"""
        try:
            # Skip if message is too short
            if len(message.content.strip()) < AUTO_DETECT_MIN_MESSAGE_LENGTH:
                return
            
            # Skip if message contains URLs (likely sharing content, not making claims)
            if 'http' in message.content.lower():
                return
            
            # Skip if message is a question (starts with question words or ends with ?)
            question_words = ['what', 'how', 'when', 'where', 'why', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did']
            first_word = message.content.strip().split()[0].lower()
            if first_word in question_words or message.content.strip().endswith('?'):
                return
            
            # Rate limiting for automatic checks (more lenient than commands)
            user_id = message.author.id
            now = datetime.utcnow()
            auto_check_limits = getattr(self, 'auto_check_limits', {})
            user_auto_limits = auto_check_limits.get(str(user_id), [])
            
            # Remove old timestamps (older than 5 minutes)
            user_auto_limits = [ts for ts in user_auto_limits if now - datetime.fromisoformat(ts) < timedelta(minutes=5)]
            
            # Check if user has exceeded auto-check limit
            if len(user_auto_limits) >= AUTO_DETECT_RATE_LIMIT:
                return
                
            # Add current timestamp
            user_auto_limits.append(now.isoformat())
            auto_check_limits[str(user_id)] = user_auto_limits
            self.auto_check_limits = auto_check_limits
            
            logger.info(f"Performing enhanced context-aware misinformation check on message from {message.author}")
            
            # Get conversation context from recent messages
            context = await self.get_conversation_context(message)
            
            # Enhanced AI analysis with context and community patterns
            analysis = await self.ai_client.analyze_with_community_context(
                message.content, 
                context,
                community_id=message.guild.id if message.guild else None
            )
            
            if not analysis:
                # Fallback to basic truthiness check
                analysis = await self.ai_client.rate_truthiness(message.content)
            
            if analysis and analysis.get('truthiness_percentage', 100) < AUTO_DETECT_TRUTHINESS_THRESHOLD:
                truthiness_score = analysis.get('truthiness_percentage', 0)
                confidence = analysis.get('confidence', 0)
                reasoning = analysis.get('reasoning', 'No reasoning provided')
                urgency = analysis.get('urgency_level', 'medium')
                spread_risk = analysis.get('spread_risk', 'unknown')
                
                # Only reply if confidence is reasonably high
                if confidence < AUTO_DETECT_CONFIDENCE_THRESHOLD:
                    return
                
                # Check for recurring misinformation patterns
                pattern_info = await self.check_misinformation_patterns(message.content, message.guild.id if message.guild else None)
                
                # Create enhanced warning embed
                embed = discord.Embed(
                    title="🚨 Community Misinformation Alert" if urgency == 'high' else "⚠️ Potential Misinformation Detected",
                    description=self.get_alert_description(urgency, spread_risk, pattern_info),
                    color=0xff4444 if urgency == 'high' else 0xe74c3c,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📊 Truthiness Score",
                    value=f"{self.create_truthiness_bar(truthiness_score)} **{truthiness_score:.1f}%** likely to be true",
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 AI Confidence",
                    value=f"{self.create_confidence_bar(confidence)} {confidence:.1%}",
                    inline=True
                )
                
                embed.add_field(
                    name="⚡ Urgency Level",
                    value=f"{self.get_urgency_emoji(urgency)} {urgency.title()}",
                    inline=True
                )
                
                embed.add_field(
                    name="🧠 Contextual Analysis",
                    value=reasoning[:400] + ("..." if len(reasoning) > 400 else ""),
                    inline=False
                )
                
                # Add pattern warning if detected
                if pattern_info.get('is_recurring'):
                    embed.add_field(
                        name="🔄 Pattern Alert",
                        value=f"Similar misinformation detected {pattern_info.get('frequency', 0)} times in this community recently.",
                        inline=False
                    )
                
                # Add community-specific advice
                embed.add_field(
                    name="💡 Community Protection",
                    value=self.get_community_advice(urgency, spread_risk),
                    inline=False
                )
                
                embed.set_footer(
                    text="Enhanced community protection • Use !expose for detailed fact-check",
                    icon_url=self.user.avatar.url if self.user.avatar else None
                )
                
                # Create enhanced feedback view
                view = self.feedback_manager.create_enhanced_feedback_view(
                    message_id=message.id,
                    user_id=message.author.id,
                    urgency=urgency
                )
                
                # Reply with appropriate mention level
                mention_author = urgency == 'high'
                await message.reply(embed=embed, view=view, mention_author=mention_author)
                
                # Log to community misinformation tracking
                await self.log_misinformation_event(message, analysis, pattern_info)
                
                logger.info(f"Enhanced misinformation alert sent for {message.author} (truthiness: {truthiness_score:.1f}%, urgency: {urgency})")
                
        except Exception as e:
            logger.error(f"Error in enhanced automatic misinformation check: {e}")
    
    async def get_conversation_context(self, message, lookback_messages=10):
        """Get recent conversation context for better analysis"""
        try:
            context = []
            async for msg in message.channel.history(limit=lookback_messages, before=message):
                if msg.content and len(msg.content.strip()) > 10:
                    context.append({
                        'author': str(msg.author),
                        'content': msg.content[:200],
                        'timestamp': msg.created_at.isoformat()
                    })
            return context[:5]  # Limit to 5 most recent relevant messages
        except:
            return []
    
    async def check_misinformation_patterns(self, content, guild_id):
        """Check for recurring misinformation patterns in the community"""
        try:
            # Load community misinformation log
            pattern_file = f'data/community_patterns_{guild_id}.json' if guild_id else 'data/patterns.json'
            patterns = {}
            
            try:
                with open(pattern_file, 'r') as f:
                    patterns = json.load(f)
            except FileNotFoundError:
                patterns = {'claims': {}, 'topics': {}}
            
            # Extract key phrases for pattern matching
            key_phrases = self.extract_key_phrases(content)
            
            # Check for similar claims
            frequency = 0
            similar_claims = []
            
            for phrase in key_phrases:
                if phrase in patterns.get('claims', {}):
                    frequency += patterns['claims'][phrase]['count']
                    similar_claims.extend(patterns['claims'][phrase]['examples'][:2])
            
            return {
                'is_recurring': frequency > 2,
                'frequency': frequency,
                'similar_claims': similar_claims,
                'key_phrases': key_phrases
            }
            
        except Exception as e:
            logger.error(f"Error checking misinformation patterns: {e}")
            return {'is_recurring': False, 'frequency': 0}
    
    def extract_key_phrases(self, content):
        """Extract key phrases from content for pattern matching"""
        # Simple keyword extraction - can be enhanced with NLP
        words = content.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Create bigrams and trigrams
        phrases = []
        for i in range(len(keywords)):
            if i < len(keywords) - 1:
                phrases.append(f"{keywords[i]} {keywords[i+1]}")
            if i < len(keywords) - 2:
                phrases.append(f"{keywords[i]} {keywords[i+1]} {keywords[i+2]}")
        
        return phrases[:5]  # Return top 5 key phrases
    
    async def log_misinformation_event(self, message, analysis, pattern_info):
        """Log misinformation event for community tracking"""
        try:
            guild_id = message.guild.id if message.guild else 'dm'
            log_file = f'data/community_patterns_{guild_id}.json'
            
            # Load existing data
            try:
                with open(log_file, 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                os.makedirs('data', exist_ok=True)
                data = {'claims': {}, 'topics': {}, 'events': []}
            
            # Log the event
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(message.author.id),
                'content_hash': hash(message.content) % 10000,  # Anonymous tracking
                'truthiness_score': analysis.get('truthiness_percentage', 0),
                'urgency': analysis.get('urgency_level', 'medium'),
                'key_phrases': pattern_info.get('key_phrases', [])
            }
            
            # Update patterns
            for phrase in pattern_info.get('key_phrases', []):
                if phrase not in data['claims']:
                    data['claims'][phrase] = {'count': 0, 'examples': []}
                data['claims'][phrase]['count'] += 1
                if len(data['claims'][phrase]['examples']) < 5:
                    data['claims'][phrase]['examples'].append(message.content[:100])
            
            # Add event (keep last 100 events)
            data['events'].append(event)
            if len(data['events']) > 100:
                data['events'] = data['events'][-100:]
            
            # Save updated data
            with open(log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging misinformation event: {e}")
    
    def get_alert_description(self, urgency, spread_risk, pattern_info):
        """Get appropriate alert description based on context"""
        if urgency == 'high':
            return "🚨 **HIGH PRIORITY**: This appears to be potentially harmful misinformation that could spread rapidly in your community."
        elif pattern_info.get('is_recurring'):
            return "🔄 **RECURRING PATTERN**: Similar misinformation has been detected multiple times in this community."
        elif spread_risk == 'high':
            return "📢 **SPREAD RISK**: This type of misinformation tends to spread quickly and may influence others."
        else:
            return "This message may contain misinformation based on AI analysis and community context."
    
    def get_urgency_emoji(self, urgency):
        """Get emoji for urgency level"""
        emojis = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴',
            'critical': '🚨'
        }
        return emojis.get(urgency, '🟡')
    
    def get_community_advice(self, urgency, spread_risk):
        """Get community-specific advice"""
        if urgency == 'high':
            return "⚠️ **Moderators**: Consider reviewing this content. **Members**: Please verify before sharing or discussing further."
        elif spread_risk == 'high':
            return "📢 **Community**: Please fact-check this information before sharing with others."
        else:
            return "💭 **Suggestion**: Verify this information with reliable sources before accepting or sharing."
    
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
        bar = "█" * filled + "░" * (10 - filled)
        return f"`{bar}`"
    
    def check_rate_limit(self, user_id):
        """Check if user is rate limited"""
        now = datetime.utcnow()
        user_limits = self.rate_limits.get(str(user_id), [])
        
        # Remove old timestamps (older than 1 minute)
        user_limits = [ts for ts in user_limits if now - datetime.fromisoformat(ts) < timedelta(minutes=1)]
        
        # Check if user has exceeded limit (5 commands per minute)
        if len(user_limits) >= 5:
            return False
            
        # Add current timestamp
        user_limits.append(now.isoformat())
        self.rate_limits[str(user_id)] = user_limits
        
        # Save rate limits
        self.save_rate_limits()
        return True
    
    def load_rate_limits(self):
        """Load rate limit data from file"""
        try:
            with open('data/rate_limits.json', 'r') as f:
                self.rate_limits = json.load(f)
        except FileNotFoundError:
            self.rate_limits = {}
            os.makedirs('data', exist_ok=True)
    
    def save_rate_limits(self):
        """Save rate limit data to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/rate_limits.json', 'w') as f:
                json.dump(self.rate_limits, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rate limits: {e}")
    
    def start_health_server(self):
        """Start HTTP server for UptimeRobot monitoring"""
        app = web.Application()
        app.router.add_get('/', self.health_check)
        app.router.add_get('/health', self.health_check)
        
        def run_server():
            web.run_app(app, host='0.0.0.0', port=5000)
        
        # Run server in separate thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info("Health check server started on port 5000 for UptimeRobot")
    
    async def health_check(self, request):
        """Health check endpoint for UptimeRobot"""
        return web.json_response({
            'status': 'online',
            'bot_ready': self.is_ready(),
            'uptime': 'Discord bot is running',
            'timestamp': datetime.utcnow().isoformat()
        })

async def main():
    """Main function to run the bot"""
    bot = FactCheckBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
