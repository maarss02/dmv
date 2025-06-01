require('dotenv').config();
const { Client, GatewayIntentBits, SlashCommandBuilder, Routes, REST, ActionRowBuilder, ButtonBuilder, ButtonStyle, Events } = require('discord.js');

const TOKEN = process.env.TOKEN;
const CLIENT_ID = '1378861465003495445'; // ID de l'application du nouveau bot
const GUILD_ID = '1370086363034161162'; // ID de ton serveur Discord

const client = new Client({
  intents: [GatewayIntentBits.Guilds]
});

client.once('ready', () => {
  console.log(`✅ Connecté en tant que ${client.user.tag}`);
});

// Enregistrer la commande /forcematchbutton
const commands = [
  new SlashCommandBuilder()
    .setName('forcematchbutton')
    .setDescription("Affiche un bouton pour forcer le lancement")
].map(cmd => cmd.toJSON());

const rest = new REST({ version: '10' }).setToken(TOKEN);
rest.put(Routes.applicationGuildCommands(CLIENT_ID, GUILD_ID), { body: commands })
  .then(() => console.log('✅ Commande slash enregistrée'))
  .catch(console.error);

// Quand quelqu'un tape /forcematchbutton
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

// Quand quelqu’un clique sur le bouton
client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isButton()) return;
  if (interaction.customId === 'force_start') {
    await interaction.channel.send('/forcestart');
    await interaction.reply({ content: '✅ Match lancé avec /forcestart', ephemeral: true });
  }
});

client.login(TOKEN);
