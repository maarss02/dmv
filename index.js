const { Client, GatewayIntentBits } = require('discord.js');


const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// Remplace par l’ID de ton salon média
const MEDIA_CHANNEL_ID = '1346899064687427736';

client.once('ready', () => {
  console.log(`✅ Connecté en tant que ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  console.log(`[LOG] Message reçu dans salon ${message.channel.id} : "${message.content}"`);

  if (message.channel.id !== MEDIA_CHANNEL_ID) {
    console.log(`[IGNORÉ] Mauvais salon`);
    return;
  }

  const hasLink = /https?:\/\//.test(message.content);
  const hasAttachment = message.attachments.size > 0;
  const hasEmbed = message.embeds.length > 0;

  console.log(`[DEBUG] Lien: ${hasLink}, Pièce jointe: ${hasAttachment}, Embed: ${hasEmbed}`);

  if (!hasLink && !hasAttachment && !hasEmbed) {
    try {
      await message.delete();
      console.log(`❌ Message supprimé`);
    } catch (err) {
      console.error(`❌ Erreur suppression :`, err);
    }
  }
});

client.login(process.env.TOKEN);


