/**
 * Fallback responses for Flora AI when OpenAI is not available
 */

export function getFallbackResponse(question: string, language: string = 'en'): string {
  const questionLower = question.toLowerCase()
  
  const fallbackResponses: Record<string, { en: string; sw: string }> = {
    maize: {
      en: "🌽 **Maize Farming Advice:**\n\nMaize typically blooms 60-70 days after planting. During flowering:\n\n• Ensure adequate moisture (critical for pollination)\n• Monitor for fall armyworm and other pests\n• The tasseling stage determines final yield\n• Check your dashboard for NDVI data to track crop health\n\nBest planting times in Kenya:\n- Long rains: March-April\n- Short rains: October-November",
      sw: "🌽 **Ushauri wa Kilimo cha Mahindi:**\n\nMahindi yanapiga maua siku 60-70 baada ya kupanda. Wakati wa kuchanua:\n\n• Hakikisha unyevu wa kutosha (muhimu kwa uchavushaji)\n• Chunguza funza wa jeshi na wadudu wengine\n• Hatua ya kutoa tone inaamua mavuno ya mwisho\n• Angalia dashibodi yako kwa data ya NDVI kufuatilia afya ya mazao\n\nMiuda bora ya kupanda nchini Kenya:\n- Mvua ndefu: Machi-Aprili\n- Mvua fupi: Oktoba-Novemba"
    },
    coffee: {
      en: "☕ **Coffee Bloom Guide:**\n\nCoffee blooms after the first rains:\n- Main bloom: March-April (long rains)\n- Secondary bloom: October-November (short rains)\n\n**During flowering:**\n• Protect flowers from heavy rain\n• Maintain soil moisture\n• Apply foliar feeding\n• Watch for Coffee Berry Disease (CBD)\n\n**Timeline:**\n- Flowering → Berry formation: 2-3 weeks\n- Green berries → Ripe cherries: 6-8 months\n\nCheck satellite data for optimal conditions!",
      sw: "☕ **Mwongozo wa Maua ya Kahawa:**\n\nKahawa huchanua baada ya mvua za kwanza:\n- Maua makuu: Machi-Aprili (mvua ndefu)\n- Maua ya pili: Oktoba-Novemba (mvua fupi)\n\n**Wakati wa kuchanua:**\n• Linda maua kutoka mvua kubwa\n• Dumisha unyevu wa udongo\n• Tumia mbolea ya majani\n• Chunguza Ugonjwa wa Tunda la Kahawa (CBD)\n\n**Ratiba:**\n- Kuchanua → Kuunda matunda: wiki 2-3\n- Matunda ya kijani → Cherry mbivu: miezi 6-8\n\nAngalia data ya setilaiti kwa hali bora!"
    },
    beans: {
      en: "🫘 **Bean Cultivation Tips:**\n\nBeans flower 4-6 weeks after planting.\n\n**Flowering Care:**\n• Ensure good drainage (beans don't like waterlogged soil)\n• Watch for bean fly during flowering\n• Avoid nitrogen fertilizer during blooming\n• Maintain consistent moisture\n\n**Varieties for Kenya:**\n- Rose Coco: 90-120 days\n- Canadian Wonder: 80-90 days\n- GLP-2: 75-85 days\n\n**Harvest:**\nWhen pods are full but before they dry completely. For dry beans, wait until pods turn brown.",
      sw: "🫘 **Vidokezo vya Kilimo cha Maharagwe:**\n\nMaharagwe huchanua wiki 4-6 baada ya kupanda.\n\n**Utunzaji Wakati wa Kuchanua:**\n• Hakikisha mtiririko mzuri wa maji (maharagwe hayapendi udongo uliojaa maji)\n• Chunguza nzi wa maharagwe wakati wa kuchanua\n• Epuka mbolea ya nitrojeni wakati wa kuchanua\n• Dumisha unyevu sawa\n\n**Aina za Kenya:**\n- Rose Coco: siku 90-120\n- Canadian Wonder: siku 80-90\n- GLP-2: siku 75-85\n\n**Mavuno:**\nMakapi yamejaa lakini kabla hayajakauka kabisa. Kwa maharagwe kavu, subiri hadi makapi yageuke kahawia."
    },
    tea: {
      en: "🍵 **Tea Farming Guide:**\n\nTea doesn't have traditional 'blooms' but produces flowers year-round.\n\n**Plucking Schedule:**\n• Pluck every 7-14 days depending on growth\n• Pick 2 leaves and a bud ('fine plucking')\n• Avoid plucking in wet conditions\n\n**Best Regions:** Kericho, Bomet, Nyeri, Murang'a\n\n**Care Tips:**\n• Maintain pH 4.5-5.5\n• Prune annually\n• Mulch to conserve moisture\n• Use satellite data to monitor crop vigor",
      sw: "🍵 **Mwongozo wa Kilimo cha Chai:**\n\nChai haina 'maua' ya kawaida lakini huzalisha maua mwaka mzima.\n\n**Ratiba ya Kukata:**\n• Kata kila siku 7-14 kulingana na ukuaji\n• Chuma majani 2 na chipukizi ('kukata vizuri')\n• Epuka kukata katika hali ya mvua\n\n**Maeneo Bora:** Kericho, Bomet, Nyeri, Murang'a\n\n**Vidokezo vya Utunzaji:**\n• Dumisha pH 4.5-5.5\n• Poda kila mwaka\n• Tumia malishio kudumisha unyevu\n• Tumia data ya setilaiti kufuatilia nguvu ya mazao"
    },
    weather: {
      en: "🌦️ **Kenya Weather & Farming:**\n\n**Rainfall Seasons:**\n• Long Rains: March-May (main planting)\n• Short Rains: October-December (second season)\n• Dry Seasons: January-February, June-September\n\n**Regional Variations:**\n• Coast: Hot & humid year-round\n• Highlands: Cool with consistent rainfall\n• Rift Valley: Varied microclimates\n• Eastern: Semi-arid, erratic rainfall\n\n📡 Check your dashboard for real-time satellite weather data!\n\n**Pro Tip:** Plant 2-3 weeks before expected rains begin.",
      sw: "🌦️ **Hali ya Hewa & Ukulima Kenya:**\n\n**Misimu ya Mvua:**\n• Mvua Ndefu: Machi-Mei (kupanda kuu)\n• Mvua Fupi: Oktoba-Disemba (msimu wa pili)\n• Misimu Kavu: Januari-Februari, Juni-Septemba\n\n**Tofauti za Mikoa:**\n• Pwani: Joto na unyevu mwaka mzima\n• Vilima: Baridi na mvua sawa\n• Bonde la Ufa: Hali ya hewa tofauti\n• Mashariki: Kame, mvua isiyotegemewa\n\n📡 Angalia dashibodi yako kwa data ya hali ya hewa kutoka setilaiti!\n\n**Kidokezo:** Panda wiki 2-3 kabla mvua hazijaanza."
    },
    bloom: {
      en: "🌸 **Bloom Detection Explained:**\n\nBloomWatch uses NASA satellite data to detect when crops are flowering:\n\n**How it works:**\n1. Sentinel-2 satellites scan your region\n2. NDVI shows vegetation health\n3. Bloom algorithms detect flowering patterns\n4. You get SMS alerts when blooms detected\n\n**Why it matters:**\n• Optimal pest management timing\n• Predict harvest dates\n• Plan labor and resources\n• Maximize pollination success\n\n📱 Enable SMS alerts in your profile to get notified!",
      sw: "🌸 **Ugunduzi wa Maua Umeelezwa:**\n\nBloomWatch inatumia data ya setilaiti ya NASA kugundua mazao yanapochanua:\n\n**Jinsi inavyofanya kazi:**\n1. Setilaiti za Sentinel-2 huchambua eneo lako\n2. NDVI inaonyesha afya ya mimea\n3. Algoriti za maua zinagundua mifumo ya kuchanua\n4. Unapata SMS yanapogundulika maua\n\n**Kwa nini ni muhimu:**\n• Muda bora wa kudhibiti wadudu\n• Kutabiri tarehe za mavuno\n• Kupanga wafanyakazi na rasilimali\n• Kuongeza mafanikio ya uchavushaji\n\n📱 Washa tahadhari za SMS kwenye wasifu wako kupata arifa!"
    },
    pest: {
      en: "🐛 **Common Pest Management:**\n\n**Fall Armyworm (Maize):**\n• Scout fields weekly\n• Apply biocontrol (neem oil, Bt)\n• Use pheromone traps\n\n**Coffee Berry Borer:**\n• Harvest all ripe cherries\n• Prune and manage shade\n• Use sticky traps\n\n**Bean Fly:**\n• Plant resistant varieties\n• Proper spacing\n• Early planting\n\n💡 Satellite data helps detect pest damage early through NDVI changes!",
      sw: "🐛 **Udhibiti wa Wadudu wa Kawaida:**\n\n**Funza wa Jeshi (Mahindi):**\n• Chunguza mashamba kila wiki\n• Tumia dhibiti wa kibiolojia (mafuta ya mwarubaini, Bt)\n• Tumia mitego ya harufu\n\n**Mdudu wa Tunda la Kahawa:**\n• Vuna cherry zote mbivu\n• Poda na simamia kivuli\n• Tumia mitego ya kunata\n\n**Nzi wa Maharagwe:**\n• Panda aina zinazostahimili\n• Nafasi sahihi\n• Kupanda mapema\n\n💡 Data ya setilaiti inasaidia kugundua uharibifu wa wadudu mapema kupitia mabadiliko ya NDVI!"
    },
    fertilizer: {
      en: "🌱 **Fertilizer Application Guide:**\n\n**NPK for Different Crops:**\n• Maize: DAP at planting, CAN top-dress at 4 weeks\n• Coffee: NPK 17:17:17 after rains\n• Tea: Nitrogen-rich, split applications\n• Beans: Light NPK, avoid excess nitrogen\n\n**Application Tips:**\n• Apply when soil is moist\n• Don't apply before heavy rain\n• Split into multiple applications\n• Band/ring application is more efficient\n\n📊 Use NDVI data to see if fertilizer is working!",
      sw: "🌱 **Mwongozo wa Matumizi ya Mbolea:**\n\n**NPK kwa Mazao Tofauti:**\n• Mahindi: DAP wakati wa kupanda, CAN juu wiki 4\n• Kahawa: NPK 17:17:17 baada ya mvua\n• Chai: Tajiri wa nitrojeni, matumizi yaligawanywa\n• Maharagwe: NPK nyepesi, epuka nitrojeni nyingi\n\n**Vidokezo vya Matumizi:**\n• Tumia wakati udongo una unyevu\n• Usitumie kabla ya mvua kubwa\n• Gawanya katika matumizi mengi\n• Matumizi ya mkanda/pete ni bora\n\n📊 Tumia data ya NDVI kuona kama mbolea inafanya kazi!"
    }
  }

  // Detect topic from question
  let response = fallbackResponses.default[language as 'en' | 'sw']
  
  if (questionLower.includes('maize') || questionLower.includes('mahindi') || questionLower.includes('corn')) {
    response = fallbackResponses.maize[language as 'en' | 'sw']
  } else if (questionLower.includes('coffee') || questionLower.includes('kahawa')) {
    response = fallbackResponses.coffee[language as 'en' | 'sw']
  } else if (questionLower.includes('bean') || questionLower.includes('maharagwe')) {
    response = fallbackResponses.beans[language as 'en' | 'sw']
  } else if (questionLower.includes('tea') || questionLower.includes('chai')) {
    response = fallbackResponses.tea[language as 'en' | 'sw']
  } else if (questionLower.includes('weather') || questionLower.includes('hali') || questionLower.includes('rain') || questionLower.includes('mvua')) {
    response = fallbackResponses.weather[language as 'en' | 'sw']
  } else if (questionLower.includes('bloom') || questionLower.includes('flower') || questionLower.includes('maua')) {
    response = fallbackResponses.bloom[language as 'en' | 'sw']
  } else if (questionLower.includes('pest') || questionLower.includes('wadudu') || questionLower.includes('insect')) {
    response = fallbackResponses.pest[language as 'en' | 'sw']
  } else if (questionLower.includes('fertilizer') || questionLower.includes('mbolea') || questionLower.includes('npk')) {
    response = fallbackResponses.fertilizer[language as 'en' | 'sw']
  }

  const prefix = language === 'sw' 
    ? "🌺 **Flora (Hali ya Demo):**\n\n" 
    : "🌺 **Flora (Demo Mode):**\n\n"

  const suffix = language === 'sw'
    ? "\n\n💡 _Ujumbe huu ni kutoka kwa mfumo wa demo. Kwa majibu ya AI kamili yenye data halisi ya setilaiti, msimamizi anahitaji kuweka ufunguo wa OpenAI API._"
    : "\n\n💡 _This is a demo response. For full AI-powered answers with real satellite data integration, the admin needs to configure the OpenAI API key._"

  return prefix + response + suffix
}


