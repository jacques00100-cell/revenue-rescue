#!/usr/bin/env node
/**
 * HVAC Lead Generator - Batch 2 (New DFW Areas)
 * Fetches HVAC companies using Google Places API (New)
 */

const API_KEY = 'AIzaSyBxlFDdKEz0zOZuLrEZgBKHl6aH2XBerBk';
const OUTPUT_FILE = '/Users/connorsisk/.openclaw/workspace/builds/revenue-rescue/research/hvac-leads-dfw-BATCH2.json';

// All search queries to maximize coverage
const SEARCH_QUERIES = [
  // Original 8 areas - primary searches
  'hvac Garland TX',
  'air conditioning Mesquite TX',
  'heating repair Carrollton TX',
  'ac service Richardson TX',
  'hvac company Irving TX',
  'air conditioning Lewisville TX',
  'heating Coppell TX',
  'ac repair Grapevine TX',
  
  // Additional variations for same areas
  'air conditioning repair Garland TX',
  'heating and cooling Mesquite TX',
  'hvac repair Carrollton TX',
  'air conditioner service Richardson TX',
  'heating company Irving TX',
  'hvac repair Lewisville TX',
  'air conditioning company Coppell TX',
  'heating repair Grapevine TX',
  
  // Broader DFW searches with location bias
  'hvac contractor Dallas',
  'air conditioning service Dallas TX',
  'heating and air Dallas',
  'ac installation Dallas',
  'hvac maintenance Dallas',
  
  // Additional city variations
  'hvac Plano TX',
  'ac repair Plano',
  'hvac Frisco TX',
  'air conditioning Allen TX',
  'hvac McKinney TX',
  'ac service Prosper TX',
  'hvac Little Elm TX',
  'air conditioning The Colony TX',
  'hvac Denton TX',
  'ac repair Denton',
  'heating Flower Mound TX',
  'hvac Highland Village TX',
  'ac service Southlake TX',
  'hvac Colleyville TX',
  'air conditioning Bedford TX',
  'hvac Euless TX',
  'ac repair Hurst TX',
  'heating North Richland Hills TX',
  'hvac Keller TX',
  'air conditioning Watauga TX',
  'ac service Haltom City TX',
  'hvac Richland Hills TX',
  'heating Arlington TX',
  'ac repair Grand Prairie TX',
  'hvac Duncanville TX',
  'air conditioning DeSoto TX',
  'ac service Lancaster TX',
  'hvac Cedar Hill TX',
  'heating Mansfield TX',
  'ac repair Burleson TX',
  'hvac Fort Worth TX',
  'air conditioning service Fort Worth',
  'heating repair Fort Worth TX'
];

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function searchPlacesNew(query) {
  const url = 'https://places.googleapis.com/v1/places:searchText';
  
  const body = {
    textQuery: query,
    locationBias: {
      circle: {
        center: {
          latitude: 32.7767,
          longitude: -96.7970
        },
        radius: 50000.0 // 50km radius to cover all DFW
      }
    }
  };
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Goog-Api-Key': API_KEY,
      'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.businessStatus'
    },
    body: JSON.stringify(body)
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`HTTP ${response.status}: ${error}`);
  }
  
  return response.json();
}

function getPriority(rating) {
  if (!rating) return 'low';
  if (rating >= 4.8) return 'high';
  if (rating >= 4.5) return 'medium';
  return 'low';
}

function normalizePlace(place) {
  return {
    company_name: place.displayName?.text || place.displayName || 'Unknown',
    phone: place.nationalPhoneNumber || place.internationalPhoneNumber || null,
    website: place.websiteUri || null,
    address: place.formattedAddress || null,
    rating: place.rating || null,
    business_status: place.businessStatus || 'OPERATIONAL',
    priority: getPriority(place.rating)
  };
}

async function fetchAllLeads() {
  const leads = new Map();
  
  console.log('Starting HVAC lead generation for Batch 2...');
  console.log(`Total search queries: ${SEARCH_QUERIES.length}`);
  
  for (let i = 0; i < SEARCH_QUERIES.length; i++) {
    const query = SEARCH_QUERIES[i];
    console.log(`\n[${i + 1}/${SEARCH_QUERIES.length}] Searching: "${query}"`);
    
    try {
      const data = await searchPlacesNew(query);
      
      if (data.places && data.places.length > 0) {
        console.log(`  Found ${data.places.length} results`);
        
        for (const place of data.places) {
          const id = place.id || place.name;
          if (!leads.has(id) && place.businessStatus !== 'CLOSED_PERMANENTLY') {
            leads.set(id, normalizePlace(place));
          }
        }
      } else {
        console.log('  No results');
      }
    } catch (err) {
      console.error(`  Error: ${err.message}`);
    }
    
    console.log(`  Total unique so far: ${leads.size}`);
    
    if (leads.size >= 200) {
      console.log('\n✅ Reached 200 leads target!');
      break;
    }
    
    await sleep(150); // Rate limiting
  }
  
  console.log(`\nTotal unique leads found: ${leads.size}`);
  
  // Filter to OPERATIONAL only
  const operationalLeads = Array.from(leads.values())
    .filter(l => l.business_status === 'OPERATIONAL' || l.business_status === null);
  
  console.log(`Operational leads: ${operationalLeads.length}`);
  
  // Sort by priority then rating
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  operationalLeads.sort((a, b) => {
    const pDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
    if (pDiff !== 0) return pDiff;
    return (b.rating || 0) - (a.rating || 0);
  });
  
  return operationalLeads;
}

async function main() {
  try {
    const leads = await fetchAllLeads();
    
    console.log('\n' + '='.repeat(50));
    console.log('LEAD GENERATION COMPLETE - BATCH 2');
    console.log('='.repeat(50));
    console.log(`Total leads generated: ${leads.length}`);
    
    const byPriority = leads.reduce((acc, l) => {
      acc[l.priority] = (acc[l.priority] || 0) + 1;
      return acc;
    }, {});
    
    console.log('\nBreakdown by priority:');
    console.log(`  High (4.8+): ${byPriority.high || 0}`);
    console.log(`  Medium (4.5-4.7): ${byPriority.medium || 0}`);
    console.log(`  Low (<4.5): ${byPriority.low || 0}`);
    
    // Sample output
    console.log('\nSample leads:');
    leads.slice(0, 3).forEach((l, i) => {
      console.log(`  ${i + 1}. ${l.company_name} (${l.priority}) - ${l.rating || 'N/A'}★`);
    });
    
    // Ensure output directory exists
    const fs = require('fs');
    const path = require('path');
    const dir = path.dirname(OUTPUT_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    // Save results
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(leads, null, 2));
    console.log(`\n✅ Saved to: ${OUTPUT_FILE}`);
    
  } catch (err) {
    console.error('Fatal error:', err);
    process.exit(1);
  }
}

main();
