# ZERO-COMP JavaScript SDK Integration Guide

This guide provides comprehensive instructions for integrating the ZERO-COMP Solar Weather API JavaScript SDK into your web applications and Node.js projects.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [Error Handling](#error-handling)
7. [Framework Integration](#framework-integration)
8. [Browser Integration](#browser-integration)
9. [Node.js Integration](#nodejs-integration)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Installation

### Node.js Environment

```bash
# Install dependencies
npm install node-fetch ws

# If using TypeScript
npm install @types/node-fetch @types/ws
```

### Browser Environment

```html
<!-- Include the SDK directly -->
<script src="path/to/javascript_sdk.js"></script>

<!-- Or use a module bundler like webpack, rollup, etc. -->
```

### ES6 Modules

```javascript
// Node.js with ES6 modules
import {
    ZeroCompClient,
    ZeroCompWebSocketClient,
    SeverityLevel,
    getCurrentAlert
} from './javascript_sdk.js';

// CommonJS (Node.js)
const {
    ZeroCompClient,
    ZeroCompWebSocketClient,
    SeverityLevel,
    getCurrentAlert
} = require('./javascript_sdk.js');
```

## Quick Start

### 1. Get Your API Key

1. Sign up at [ZERO-COMP Dashboard](https://dashboard.zero-comp.com)
2. Navigate to API Keys section
3. Generate a new API key
4. Store it securely

### 2. Basic Example

```javascript
// Node.js
const { ZeroCompClient } = require('./javascript_sdk');

// Browser
const client = new ZeroComp.ZeroCompClient({
    apiKey: 'your-api-key-here'
});

// Get current solar flare probability
async function getCurrentSolarWeather() {
    try {
        const alert = await client.getCurrentAlert();
        console.log(`Solar flare probability: ${(alert.currentProbability * 100).toFixed(1)}%`);
        console.log(`Severity: ${alert.severityLevel}`);
        console.log(`Alert active: ${alert.alertActive}`);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

getCurrentSolarWeather();
```

## Authentication

### API Key Confi