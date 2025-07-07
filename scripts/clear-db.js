const mongoose = require('mongoose');
require('dotenv').config();

const User = require('../models/User');
const Business = require('../models/Business');
const Deal = require('../models/Deal');

async function clearDatabase() {
  try {
    // Connect to database
    await mongoose.connect(process.env.MONGO_URI);
    console.log('✅ Connected to database');

    // Delete all documents from each collection
    const userResult = await User.deleteMany({});
    console.log(`🗑️  Deleted ${userResult.deletedCount} users`);

    const businessResult = await Business.deleteMany({});
    console.log(`🗑️  Deleted ${businessResult.deletedCount} businesses`);

    const dealResult = await Deal.deleteMany({});
    console.log(`🗑️  Deleted ${dealResult.deletedCount} deals`);

    console.log('✅ Database cleared successfully');
  } catch (error) {
    console.error('❌ Error clearing database:', error);
  } finally {
    await mongoose.disconnect();
    console.log('🔌 Disconnected from database');
  }
}

clearDatabase(); 