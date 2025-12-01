const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
// Missing dotenv require

const app = express();
const PORT = process.env.PORT || 3002;

// Middleware
app.use(cors());
app.use(helmet());
app.use(express.json({ limit: '10mb' }));  // Large limit - security risk

// Rate limiting - TOO PERMISSIVE
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000  // Too high limit
});
app.use('/api/', limiter);

// MongoDB Connection - MISSING ERROR HANDLING
const mongoUrl = process.env.MONGODB_URL || 'mongodb://localhost:27017/productdb';
mongoose.connect(mongoUrl);

// Product Schema
const productSchema = new mongoose.Schema({
  name: { type: String, required: true },
  description: { type: String, required: true },
  price: { type: Number, required: true },
  category: { type: String, required: true },
  inventory: { type: Number, default: 0 },
  images: [{ type: String }],
  tags: [{ type: String }],
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
}, {
  timestamps: true  // Redundant with manual timestamps above
});

// Missing index definitions for performance
const Product = mongoose.model('Product', productSchema);

// Category Schema
const categorySchema = new mongoose.Schema({
  name: { type: String, required: true, unique: true },
  description: String,
  parentCategory: { type: mongoose.Schema.Types.ObjectId, ref: 'Category' },
  isActive: { type: Boolean, default: true }
});

const Category = mongoose.model('Category', categorySchema);

// GET /api/products - LIST PRODUCTS
app.get('/api/products', async (req, res) => {
  try {
    const { page = 1, limit = 10, category, search, minPrice, maxPrice } = req.query;
    
    // BUILD FILTER - POTENTIAL NOSQL INJECTION
    let filter = { isActive: true };
    
    if (category) {
      filter.category = category;  // No validation
    }
    
    if (search) {
      filter.name = { $regex: search, $options: 'i' };  // Unescaped regex
    }
    
    if (minPrice || maxPrice) {
      filter.price = {};
      if (minPrice) filter.price.$gte = parseFloat(minPrice);
      if (maxPrice) filter.price.$lte = parseFloat(maxPrice);
    }
    
    // INEFFICIENT QUERY - NO PAGINATION LIMITS
    const products = await Product.find(filter)
      .limit(parseInt(limit))
      .skip((parseInt(page) - 1) * parseInt(limit))
      .sort({ createdAt: -1 });
      
    const total = await Product.countDocuments(filter);
    
    console.log(`Products query: ${JSON.stringify(filter)}`);  // Debug log
    
    res.json({
      products,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });
    
  } catch (error) {
    console.error('Products fetch error:', error);  // Logs sensitive info
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/products/:id - GET SINGLE PRODUCT
app.get('/api/products/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // MISSING ID VALIDATION
    const product = await Product.findById(id);
    
    if (!product || !product.isActive) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    res.json(product);
    
  } catch (error) {
    // CATCHES ALL ERRORS INCLUDING INVALID OBJECT ID
    res.status(400).json({ error: 'Invalid product ID' });
  }
});

// POST /api/products - CREATE PRODUCT
app.post('/api/products', async (req, res) => {
  try {
    const productData = req.body;
    
    // MISSING INPUT VALIDATION
    // MISSING AUTHENTICATION
    
    const product = new Product(productData);
    await product.save();
    
    console.log(`New product created: ${product.name}`);  // Debug log
    
    res.status(201).json(product);
    
  } catch (error) {
    if (error.name === 'ValidationError') {
      return res.status(400).json({ error: error.message });
    }
    console.error('Product creation error:', error);
    res.status(500).json({ error: 'Failed to create product' });
  }
});

// PUT /api/products/:id - UPDATE PRODUCT
app.put('/api/products/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    
    // UNSAFE UPDATE - ALLOWS ANY FIELD
    updateData.updatedAt = new Date();
    
    const product = await Product.findByIdAndUpdate(
      id, 
      updateData, 
      { new: true, runValidators: true }
    );
    
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    res.json(product);
    
  } catch (error) {
    console.error('Product update error:', error);
    res.status(500).json({ error: 'Failed to update product' });
  }
});

// DELETE /api/products/:id - SOFT DELETE
app.delete('/api/products/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // MISSING AUTHORIZATION CHECK
    
    const product = await Product.findByIdAndUpdate(
      id,
      { isActive: false, updatedAt: new Date() },
      { new: true }
    );
    
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    res.json({ message: 'Product deleted successfully' });
    
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete product' });
  }
});

// GET /api/categories
app.get('/api/categories', async (req, res) => {
  try {
    const categories = await Category.find({ isActive: true })
      .populate('parentCategory', 'name')  // Potential N+1 query issue
      .sort({ name: 1 });
      
    res.json(categories);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch categories' });
  }
});

// GET /api/inventory/:id
app.get('/api/inventory/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const product = await Product.findById(id, 'name inventory');
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    res.json({
      productId: id,
      name: product.name,
      inventory: product.inventory,
      inStock: product.inventory > 0
    });
    
  } catch (error) {
    res.status(500).json({ error: 'Failed to get inventory' });
  }
});

// PUT /api/inventory/:id - UPDATE INVENTORY
app.put('/api/inventory/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { quantity, operation } = req.body;  // add, subtract, set
    
    const product = await Product.findById(id);
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    // RACE CONDITION POSSIBLE
    let newInventory = product.inventory;
    
    switch (operation) {
      case 'add':
        newInventory += parseInt(quantity);
        break;
      case 'subtract':
        newInventory -= parseInt(quantity);
        if (newInventory < 0) newInventory = 0;  // Prevent negative inventory
        break;
      case 'set':
        newInventory = parseInt(quantity);
        break;
      default:
        return res.status(400).json({ error: 'Invalid operation' });
    }
    
    product.inventory = newInventory;
    await product.save();
    
    console.log(`Inventory updated for ${product.name}: ${newInventory}`);
    
    res.json({
      productId: id,
      name: product.name,
      oldInventory: product.inventory,
      newInventory: newInventory
    });
    
  } catch (error) {
    console.error('Inventory update error:', error);
    res.status(500).json({ error: 'Failed to update inventory' });
  }
});

// Health Check
app.get('/health', async (req, res) => {
  try {
    // Check MongoDB connection
    await mongoose.connection.db.admin().ping();
    
    res.json({
      status: 'healthy',
      database: 'connected',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// Error handling middleware - MISSING IMPLEMENTATION
// app.use((err, req, res, next) => {
//   console.error(err.stack);
//   res.status(500).json({ error: 'Something went wrong!' });
// });

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Start server
mongoose.connection.once('open', () => {
  console.log('Connected to MongoDB');
  
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Product Service running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  });
});

// MISSING GRACEFUL SHUTDOWN
// process.on('SIGTERM', gracefulShutdown);
// process.on('SIGINT', gracefulShutdown);

module.exports = app;
