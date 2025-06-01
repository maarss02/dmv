// Bot secondaire pour bouton "Forcer le lancement" avec Webhook (envoie dans un salon fixe)

require('dotenv').config();
const { Client, GatewayIntentBits, SlashCommandBuilder, Routes, REST, ActionRowBuilder, ButtonBuilder, ButtonStyle, Events } = require('discord.js');

const TOKEN = process.env.TOKEN;
const CLIENT_ID = '1378861465003495445'; // Ton ID de bot secondaire
const GUILD_ID = '1370086363034161162'; // Remplace par l'ID de ton serveur
const TARGET_CHANNEL_ID = '1370153731898998945'; // Remplace par l'ID du salon où tu veux envoyer /forcestart

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages]
});

client.once('ready', () => {
  console.log(`✅ Connecté en tant que ${client.user.tag}`);
});

// Enregistre la commande /forcematchbutton
const commands = [
  new SlashCommandBuilder()
    .setName('forcematchbutton')
    .setDescription("Affiche un bouton pour forcer le lancement")
].map(cmd => cmd.toJSON());

const rest = new REST({ version: '10' }).setToken(TOKEN);
rest.put(Routes.applicationGuildCommands(CLIENT_ID, GUILD_ID), { body: commands })
  .then(() => console.log('✅ Commande slash enregistrée'))
  .catch(console.error);

// Quand on tape /forcematchbutton => afficher le bouton
client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  if (interaction.commandName === 'forcematchbutton') {
    const button = new ButtonBuilder()
      .setCustomId('force_start')
      .setLabel('📢 Forcer le lancement')
      .setStyle(ButtonStyle.Danger);

    const row = new ActionRowBuilder().addComponents(button);

    await interaction.reply({
      content: 'Clique ici pour forcer le lancement du match :',
      components: [row],
    });
  }
});

// Quand on clique sur le bouton => envoie /forcestart via webhook dans le salon spécifique
client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isButton()) return;
  if (interaction.customId === 'force_start') {
    try {
      const targetChannel = await client.channels.fetch(TARGET_CHANNEL_ID);
      if (!targetChannel || !targetChannel.isTextBased()) throw new Error("Salon cible introuvable ou non textuel.");

      // Créer un webhook s'il n'existe pas déjà
      const webhooks = await targetChannel.fetchWebhooks();
      let hook = webhooks.find(wh => wh.name === 'LanceurMatch');

      if (!hook) {
        hook = await targetChannel.createWebhook({
          name: 'LanceurMatch',
          avatar: client.user.displayAvatarURL(),
        });
      }

      // Envoie /forcestart via webhook (NeatQueue peut le capter s’il est configuré pour)
      await hook.send({
        content: '/forcestart'
      });

      await interaction.reply({ content: '✅ Match lancé via webhook dans #matchs', ephemeral: true });
    } catch (err) {
      console.error('Erreur bouton :', err);
      await interaction.reply({ content: '❌ Erreur lors du lancement.', ephemeral: true });
    }
  }
});

client.login(TOKEN);
