/**
 * NeuroSign-HMI: Interactive 15-Gesture & 11-Language Indic Simulation Engine
 * Simulates 60 FPS Hand Skeleton, 1D-LSTM Inference, Web Speech Indic TTS,
 * 8x13 LED Matrix Glyphs, and STM32 Actuation in the browser.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── 1. 11 Indian Languages Translation Matrix ────────────────────────────
    const INDIC_LANGUAGES = {
        hi: { code: 'hi-IN', name: 'Hindi', native: 'हिंदी', flag: '🇮🇳' },
        bn: { code: 'bn-IN', name: 'Bengali', native: 'বাংলা', flag: '🇮🇳' },
        ta: { code: 'ta-IN', name: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
        te: { code: 'te-IN', name: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
        mr: { code: 'mr-IN', name: 'Marathi', native: 'मराठी', flag: '🇮🇳' },
        gu: { code: 'gu-IN', name: 'Gujarati', native: 'ગુજરાતી', flag: '🇮🇳' },
        kn: { code: 'kn-IN', name: 'Kannada', native: 'ಕನ್ನಡ', flag: '🇮🇳' },
        ml: { code: 'ml-IN', name: 'Malayalam', native: 'മലയാളം', flag: '🇮🇳' },
        pa: { code: 'pa-IN', name: 'Punjabi', native: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
        or: { code: 'or-IN', name: 'Odia', native: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
        en: { code: 'en-US', name: 'English', native: 'English', flag: '🌐' }
    };

    let activeLang = 'hi';

    // ── 2. 15 Gesture Configurations & Multi-Lingual Phrases ─────────────────
    const GESTURES = [
        {
            id: 0, key: 'sos', icon: '🚨',
            name_en: 'Emergency - Need Help',
            phrases: {
                en: 'Emergency! I need urgent help immediately!',
                hi: 'आपातकाल! मुझे तुरंत सहायता की आवश्यकता है!',
                bn: 'জরুরী অবস্থা! আমার অবিলম্বে সাহায্য প্রয়োজন!',
                ta: 'அவசரம்! எனக்கு உடனடியாக உதவி தேவை!',
                te: 'అత్యవసరం! నాకు వెంటనే సహాయం కావాలి!',
                mr: 'आणीबाणी! मला ताबडतोब मदतीची गरज आहे!',
                gu: 'કટોકટી! મને તાત્કાલિક મદદની જરૂર છે!',
                kn: 'ತುರ್ತು! ನನಗೆ ತಕ್ಷಣ ಸಹಾಯ ಬೇಕು!',
                ml: 'അടിയന്തിരം! എനിക്ക് ഉടൻ സഹായം വേണം!',
                pa: 'ਐਮਰਜੈਂਸੀ! ਮੈਨੂੰ ਤੁਰੰਤ ਮਦਦ ਚਾਹੀਦੀ ਹੈ!',
                or: 'ଜରୁରୀକାଳୀନ! ମୋତେ ତୁରନ୍ତ ସାହାଯ୍ୟ ଦରକାର!'
            },
            relay1: true, relay2: true, pan: 90, tilt: 105, gsm: 'SMS SENT: +919876543210', matrixType: 'sos',
            joints: getHandPoseSOS()
        },
        {
            id: 1, key: 'light_on', icon: '💡',
            name_en: 'Turn On Room Light',
            phrases: {
                en: 'Please turn on the room light.',
                hi: 'कृपया कमरे की लाइट चालू कर दीजिए।',
                bn: 'দয়া করে ঘরের আলো জ্বালিয়ে দিন।',
                ta: 'தயவுசெய்து அறையின் விளக்கை போடுங்கள்.',
                te: 'దయచేసి గదిలోని లైట్ వేయండి.',
                mr: 'कृपया खोलीतील लाइट चालू करा.',
                gu: 'કૃપા કરીને રૂમની લાઇટ ચાલુ કરો.',
                kn: 'ದಯವಿಟ್ಟು ಕೋಣೆಯ ಲೈಟ್ ಆನ್ ಮಾಡಿ.',
                ml: 'ദയവായി മുറിയിലെ ലൈറ്റ് ഓൺ ചെയ്യുക.',
                pa: 'ਕਿਰਪਾ ਕਰਕੇ ਕਮਰੇ ਦੀ ਲਾਈਟ ਆਨ ਕਰ ਦਿਓ।',
                or: 'ଦୟାକରି ରୁମର ଲାଇଟ୍ ଲଗାନ୍ତୁ।'
            },
            relay1: true, relay2: false, pan: 110, tilt: 92, gsm: 'Standby', matrixType: 'relay_on',
            joints: getHandPoseOpenPalm()
        },
        {
            id: 2, key: 'light_off', icon: '🌑',
            name_en: 'Turn Off Room Light',
            phrases: {
                en: 'Please turn off the room light.',
                hi: 'कृपया कमरे की लाइट बंद कर दीजिए।',
                bn: 'দয়া করে ঘরের আলো নিভিয়ে দিন।',
                ta: 'தயவுசெய்து அறையின் விளக்கை அணைக்கவும்.',
                te: 'దయచేసి గదిలోని లైట్ ఆపండి.',
                mr: 'कृपया खोलीतील लाइट बंद करा.',
                gu: 'કૃપા કરીને રૂમની લાઇટ બંધ કરો.',
                kn: 'ದಯವಿಟ್ಟು ಕೋಣೆಯ ಲೈಟ್ ಆಫ್ ಮಾಡಿ.',
                ml: 'ദയവായി മുറിയിലെ ലൈറ്റ് ഓഫ് ചെയ്യുക.',
                pa: 'ਕਿਰਪਾ ਕਰਕੇ ਕਮਰੇ ਦੀ ਲਾਈਟ ਬੰਦ ਕਰ ਦਿਓ।',
                or: 'ଦୟାକରି ରୁମର ଲାଇଟ୍ ବନ୍ଦ କରନ୍ତୁ।'
            },
            relay1: false, relay2: false, pan: 80, tilt: 90, gsm: 'Standby', matrixType: 'idle',
            joints: getHandPoseFist()
        },
        {
            id: 3, key: 'water', icon: '💧',
            name_en: 'Water Please',
            phrases: {
                en: 'Could you please give me a glass of water?',
                hi: 'कृपया मुझे एक गिलास पानी दीजिए।',
                bn: 'দয়া করে আমাকে এক গ্লাস জল দিন।',
                ta: 'தயவுசெய்து எனக்கு தண்ணீர் கொடுங்கள்.',
                te: 'దయచేసి నాకు ఒక గ్లాసు నీళ్ళు ఇవ్వండి.',
                mr: 'कृपया मला एक ग्लास पाणी द्या.',
                gu: 'કૃપા કરીને મને એક ગ્લાસ પાણી આપો.',
                kn: 'ದಯವಿಟ್ಟು ನನಗೆ ಒಂದು ಲೋಟ ನೀರು ಕೊಡಿ.',
                ml: 'ദയവായി എനിക്ക് ഒരു ഗ്ലാസ് വെള്ളം തരൂ.',
                pa: 'ਕਿਰਪਾ ਕਰਕੇ ਮੈਨੂੰ ਇੱਕ ਗਲਾਸ ਪਾਣੀ ਦਿਓ।',
                or: 'ଦୟାକରି ମୋତେ ଗୋଟିଏ ଗ୍ଲାସ ପାଣି ଦିଅନ୍ତୁ।'
            },
            relay1: false, relay2: false, pan: 95, tilt: 88, gsm: 'Standby', matrixType: 'check',
            joints: getHandPoseWater()
        },
        {
            id: 4, key: 'thanks', icon: '🙏',
            name_en: 'Thank You',
            phrases: {
                en: 'Thank you very much!',
                hi: 'आपका बहुत-बहुत धन्यवाद!',
                bn: 'আপনাকে অনেক ধন্যবাদ!',
                ta: 'உங்களுக்கு மிக்க நன்றி!',
                te: 'మీకు చాలా ధన్యవాదాలు!',
                mr: 'आपले खूप खूप धन्यवाद!',
                gu: 'તમારો ખૂબ ખૂબ આભાર!',
                kn: 'ನಿಮಗೆ ತುಂಬಾ ಧನ್ಯವಾದಗಳು!',
                ml: 'നിങ്ങൾക്ക് വളരെ നന്ദി!',
                pa: 'ਤੁਹਾਡਾ ਬਹੁਤ ਬਹੁਤ ਧੰਨਵਾਦ!',
                or: 'ଆପଣଙ୍କୁ ବହୁତ ବହୁତ ଧନ୍ୟବାଦ!'
            },
            relay1: false, relay2: false, pan: 90, tilt: 85, gsm: 'Standby', matrixType: 'check',
            joints: getHandPoseThanks()
        },
        {
            id: 5, key: 'yes', icon: '👍',
            name_en: 'Yes / Affirmative',
            phrases: {
                en: 'Yes, affirmative.',
                hi: 'हाँ, बिल्कुल।',
                bn: 'হ্যাঁ, নিশ্চয়ই।',
                ta: 'ஆம், சரி.',
                te: 'అవును, అలాగే।',
                mr: 'होय, नक्कीच.',
                gu: 'હા, ચોક્કસ.',
                kn: 'ಹೌದು, ಖಂಡಿತ.',
                ml: 'അതെ, ശരിയാണ്.',
                pa: 'ਹਾਂ ਜੀ, ਬਿਲਕੁਲ।',
                or: 'ହଁ, ନିଶ୍ଚୟ।'
            },
            relay1: false, relay2: false, pan: 92, tilt: 94, gsm: 'Standby', matrixType: 'check',
            joints: getHandPoseThumbsUp()
        },
        {
            id: 6, key: 'no', icon: '✋',
            name_en: 'No / Decline',
            phrases: {
                en: 'No, thank you.',
                hi: 'नहीं, धन्यवाद।',
                bn: 'না, ধন্যবাদ।',
                ta: 'இல்லை, நன்றி.',
                te: 'వద్దు, ధన్యవాదాలు.',
                mr: 'नाही, धन्यवाद.',
                gu: 'ના, આભાર.',
                kn: 'ಇಲ್ಲ, ಧನ್ಯವಾದಗಳು.',
                ml: 'ഇല്ല, നന്ദി.',
                pa: 'ਨਹੀਂ, ਧੰਨਵਾਦ।',
                or: 'ନାହିଁ, ଧନ୍ୟବାଦ।'
            },
            relay1: false, relay2: false, pan: 85, tilt: 90, gsm: 'Standby', matrixType: 'cross',
            joints: getHandPoseNo()
        },
        {
            id: 7, key: 'food', icon: '🍲',
            name_en: 'Food Please',
            phrases: {
                en: 'I am hungry, please bring me some food.',
                hi: 'मुझे भूख लगी है, कृपया खाना लाइए।',
                bn: 'আমার খিদে পেয়েছে, দয়া করে খাবার দিন।',
                ta: 'எனக்கு பசிக்கிறது, தயவுசெய்து உணவு கொடுங்கள்.',
                te: 'నాకు ఆకలిగా ఉంది, దయచేసి ఆహారం తీసుకురండి.',
                mr: 'मला भूक लागली आहे, कृपया जेवण द्या.',
                gu: 'મને ભૂખ લાગી છે, કૃપા કરીને જમવાનું લાવો.',
                kn: 'ನನಗೆ ಹಸಿವಾಗಿದೆ, ದಯವಿಟ್ಟು ಊಟ ತಂದುಕೊಡಿ.',
                ml: 'എനിക്ക് വിശക്കുന്നു, ദയവായി ഭക്ഷണം തരൂ.',
                pa: 'ਮੈਨੂੰ ਭੁੱਖ ਲੱਗੀ ਹੈ, ਕਿਰਪਾ ਕਰਕੇ ਖਾਣਾ ਲਿਆਓ।',
                or: 'ମୋତେ ଭୋକ ଲାଗୁଛି, ଦୟାକରି ଖାଦ୍ୟ ଦିଅନ୍ତୁ।'
            },
            relay1: false, relay2: false, pan: 96, tilt: 86, gsm: 'Standby', matrixType: 'check',
            joints: getHandPosePinch()
        },
        {
            id: 8, key: 'medicine', icon: '💊',
            name_en: 'Medicine / Doctor',
            phrases: {
                en: 'I need my medicine or doctor assistance.',
                hi: 'मुझे मेरी दवाई और डॉक्टर की आवश्यकता है।',
                bn: 'আমার ওষুধ এবং ডাক্তারের সাহায্য দরকার।',
                ta: 'எனக்கு மருந்து அல்லது மருத்துவர் உதவி தேவை.',
                te: 'నాకు మందులు లేదా డాక్టర్ సహాయం కావాలి.',
                mr: 'मला माझे औषध आणि डॉक्टरची गरज आहे.',
                gu: 'મને મારી દવા અને ડૉક્ટરની જરૂર છે.',
                kn: 'ನನಗೆ ಔಷಧಿ ಅಥವಾ ವೈದ್ಯರ ಸಹಾಯ ಬೇಕು.',
                ml: 'എനിക്ക് മരുന്നും ഡോക്ടറുടെ സഹായവും വേണം.',
                pa: 'ਮੈਨੂੰ ਮੇਰੀ ਦਵਾਈ ਅਤੇ ਡਾਕਟਰ ਦੀ ਲੋੜ ਹੈ।',
                or: 'ମୋତେ ମୋର ଔଷଧ ଏବଂ ଡାକ୍ତରଙ୍କ ସାହାଯ୍ୟ ଦରକାର।'
            },
            relay1: false, relay2: false, pan: 92, tilt: 90, gsm: 'Standby', matrixType: 'check',
            joints: getHandPoseMedicine()
        },
        {
            id: 9, key: 'pain', icon: '⚡',
            name_en: 'Severe Pain',
            phrases: {
                en: 'I am experiencing severe pain, please help!',
                hi: 'मुझे बहुत तेज दर्द हो रहा है, कृपया मदद कीजिए!',
                bn: 'আমার খুব তীব্র ব্যথা হচ্ছে, দয়া করে সাহায্য করুন!',
                ta: 'எனக்கு கடுமையான வலி உள்ளது, தயவுசெய்து உதவுங்கள்!',
                te: 'నాకు తీవ్రమైన నొప్పిగా ఉంది, దయచేసి సహాయం చేయండి!',
                mr: 'मला खूप तीव्र वेदना होत आहेत, कृपया मदत करा!',
                gu: 'મને ખૂબ જ દુખાવો થાય છે, કૃપા કરીને મદદ કરો!',
                kn: 'ನನಗೆ ವಿಪರೀತ ನೋವಾಗುತ್ತಿದೆ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ!',
                ml: 'എനിക്ക് കഠിനമായ വേദനയുണ്ട്, ദയവായി സഹായിക്കൂ!',
                pa: 'ਮੈਨੂੰ ਬਹੁਤ ਤੇਜ਼ ਦਰਦ ਹੋ ਰਿਹਾ ਹੈ, ਕਿਰਪਾ ਕਰਕੇ ਮਦਦ ਕਰੋ!',
                or: 'ମୋତେ ପ୍ରବଳ ଯନ୍ତ୍ରଣା ହେଉଛି, ଦୟାକରି ସାହାଯ୍ୟ କରନ୍ତୁ!'
            },
            relay1: false, relay2: false, pan: 90, tilt: 95, gsm: 'Standby', matrixType: 'sos',
            joints: getHandPoseTremor()
        },
        {
            id: 10, key: 'fan_on', icon: '🌀',
            name_en: 'Turn On Fan / AC',
            phrases: {
                en: 'Please turn on the fan or air conditioning.',
                hi: 'कृपया पंखा या एसी चालू कर दीजिए।',
                bn: 'দয়া করে পাখা বা এসি চালু করুন।',
                ta: 'தயவுசெய்து விசிறி அல்லது ஏசியை போடவும்.',
                te: 'దయచేసి ఫ్యాన్ లేదా ఏసీ ఆన్ చేయండి.',
                mr: 'कृपया पंखा किंवा एसी चालू करा.',
                gu: 'કૃપા કરીને પંખો અથવા એસી ચાલુ કરો.',
                kn: 'ದಯವಿಟ್ಟು ಫ್ಯಾನ್ ಅಥವಾ ಎಸಿ ಆನ್ ಮಾಡಿ.',
                ml: 'ദയവായി ഫാൻ അല്ലെങ്കിൽ എസി ഓൺ ചെയ്യുക.',
                pa: 'ਕਿਰਪਾ ਕਰਕੇ ਪੱਖਾ ਜਾਂ ਏਸੀ ਚਲਾਓ।',
                or: 'ଦୟାକରି ପଙ୍ଖା କିମ୍ବା ଏସି ଚଲାନ୍ତୁ।'
            },
            relay1: false, relay2: true, pan: 105, tilt: 90, gsm: 'Standby', matrixType: 'relay_on',
            joints: getHandPoseFan()
        },
        {
            id: 11, key: 'fan_off', icon: '⏹️',
            name_en: 'Turn Off Fan / AC',
            phrases: {
                en: 'Please turn off the fan or air conditioning.',
                hi: 'कृपया पंखा या एसी बंद कर दीजिए।',
                bn: 'দয়া করে পাখা বা এসি বন্ধ করুন।',
                ta: 'தயவுசெய்து விசிறியை நிறுத்தவும்.',
                te: 'దయచేసి ఫ్యాన్ లేదా ఏసీ ఆపండి.',
                mr: 'कृपया पंखा किंवा एसी बंद करा.',
                gu: 'કૃપા કરીને પંખો અથવા એસી બંધ કરો.',
                kn: 'ದಯವಿಟ್ಟು ಫ್ಯಾನ್ ಅಥವಾ ಎಸಿ ಆಫ್ ಮಾಡಿ.',
                ml: 'ദയവായി ഫാൻ ഓഫ് ചെയ്യുക.',
                pa: 'ਕਿਰਪਾ ਕਰਕੇ ਪੱਖਾ ਜਾਂ ਏਸੀ ਬੰਦ ਕਰੋ।',
                or: 'ଦୟାକରି ପଙ୍ଖା ବନ୍ଦ କରନ୍ତୁ।'
            },
            relay1: false, relay2: false, pan: 88, tilt: 90, gsm: 'Standby', matrixType: 'idle',
            joints: getHandPoseFist()
        },
        {
            id: 12, key: 'washroom', icon: '🚻',
            name_en: 'Washroom Assistance',
            phrases: {
                en: 'I need assistance to go to the washroom.',
                hi: 'मुझे शौचालय जाने के लिए सहायता चाहिए।',
                bn: 'আমার শৌচালয়ে যাওয়ার জন্য সাহায্য প্রয়োজন।',
                ta: 'எனக்கு கழிப்பறை செல்ல உதவி தேவை.',
                te: 'నాకు వాష్‌రూమ్‌కు వెళ్ళడానికి సహాయం కావాలి.',
                mr: 'मला वॉशरुमला जाण्यासाठी मदतीची गरज आहे.',
                gu: 'મને શૌચાલય જવા માટે મદદની જરૂર છે.',
                kn: 'ನನಗೆ ವಾಶ್‌ರೂಮ್‌ಗೆ ಹೋಗಲು ಸಹಾಯ ಬೇಕು.',
                ml: 'എനിക്ക് വാഷ്‌റൂമിൽ പോകാൻ സഹായം വേണം.',
                pa: 'ਮੈਨੂੰ ਵਾਸ਼ਰੂਮ ਜਾਣ ਲਈ ਮਦਦ ਚਾਹੀਦੀ ਹੈ।',
                or: 'ମୋତେ ଶୌଚାଳୟ ଯିବା ପାଇଁ ସାହାଯ୍ୟ ଦରକାର।'
            },
            relay1: false, relay2: false, pan: 90, tilt: 90, gsm: 'Standby', matrixType: 'check',
            joints: getHandPoseWashroom()
        },
        {
            id: 13, key: 'call_family', icon: '📞',
            name_en: 'Call Family / Caregiver',
            phrases: {
                en: 'Please call my family or caregiver.',
                hi: 'कृपया मेरे परिवार या देखभालकर्ता को फोन करें।',
                bn: 'দয়া করে আমার পরিবার বা সেবককে ফোন করুন।',
                ta: 'தயவுசெய்து என் குடும்பத்தினரை அழைக்கவும்.',
                te: 'దయచేసి నా కుటుంబ సభ్యులకు కాల్ చేయండి.',
                mr: 'कृपया माझ्या कुटुंबाला किंवा काळजीवाहकाला फोन करा.',
                gu: 'કૃપા કરીને મારા પરિવારને ફોન કરો.',
                kn: 'ದಯವಿಟ್ಟು ನನ್ನ ಕುಟುಂಬಕ್ಕೆ ಕರೆ ಮಾಡಿ.',
                ml: 'ദയവായി എന്റെ കുടുംബത്തെയോ പരിചാരകനെയോ വിളിക്കൂ.',
                pa: 'ਕਿਰਪਾ ਕਰਕੇ ਮੇਰੇ ਪਰਿਵਾਰ ਨੂੰ ਫੋਨ ਕਰੋ।',
                or: 'ଦୟାକରି ମୋ ପରିବାର କିମ୍ବା ଯତ୍ନନେଉଥିବା ବ୍ୟକ୍ତିଙ୍କୁ ଫୋନ କରନ୍ତୁ।'
            },
            relay1: false, relay2: false, pan: 94, tilt: 92, gsm: 'Standby', matrixType: 'check',
            joints: getHandPosePhone()
        },
        {
            id: 14, key: 'sleep', icon: '😴',
            name_en: 'Sleep / Rest',
            phrases: {
                en: 'I want to rest and sleep now, thank you.',
                hi: 'मैं अब आराम करना और सोना चाहता हूँ, धन्यवाद।',
                bn: 'আমি এখন বিশ্রাম নিতে ও ঘুমাতে চাই, ধন্যবাদ।',
                ta: 'நான் இப்போது ஓய்வெடுக்கவும் தூங்கவும் விரும்புகிறேன், நன்றி.',
                te: 'నేను ఇప్పుడు విశ్రాంతి తీసుకొని నిద్రపోవాలనుకుంటున్నాను, ధన్యవాదాలు.',
                mr: 'मला आता विश्रांती घ्यायची आहे आणि झोपायचे आहे, धन्यवाद.',
                gu: 'હું હવે આરામ કરવા અને સૂવા માંગુ છું, આભાર.',
                kn: 'ನಾನು ಈಗ ವಿಶ್ರಾಂತಿ ತೆಗೆದುಕೊಂಡು ಮಲಗಲು ಬಯಸುತ್ತೇನೆ, ಧನ್ಯವಾದಗಳು.',
                ml: 'എനിക്ക് ഇപ്പോൾ വിശ്രമിക്കാനും ഉറങ്ങാനും ആഗ്രഹമുണ്ട്, നന്ദി.',
                pa: 'ਮੈਂ ਹੁਣ ਆਰਾਮ ਕਰਨਾ ਅਤੇ ਸੌਣਾ ਚਾਹੁੰਦਾ ਹਾਂ, ਧੰਨਵਾਦ।',
                or: 'ମୁଁ ଏବେ ବିଶ୍ରାମ ନେବାକୁ ଏବଂ ଶୋଇବାକୁ ଚାହୁଁଛି, ଧନ୍ୟବାଦ।'
            },
            relay1: false, relay2: false, pan: 90, tilt: 85, gsm: 'Standby', matrixType: 'idle',
            joints: getHandPoseSleep()
        }
    ];

    let currentGesture = GESTURES[3]; // Default: Water
    let targetJoints = currentGesture.joints;
    let currentJoints = JSON.parse(JSON.stringify(targetJoints));

    // MediaPipe Hand Connection Graph (21 Landmarks)
    const HAND_CONNECTIONS = [
        [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
        [0, 5], [5, 6], [6, 7], [7, 8],       // Index
        [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
        [9, 13], [13, 14], [14, 15], [15, 16],// Ring
        [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
        [0, 17]                               // Palm base
    ];

    // ── 3. Render Language Chips & 15 Gesture Buttons ──────────────────────
    const langChipsContainer = document.getElementById('langChips');
    Object.keys(INDIC_LANGUAGES).forEach(langKey => {
        const lang = INDIC_LANGUAGES[langKey];
        const btn = document.createElement('button');
        btn.className = `lang-chip ${langKey === activeLang ? 'active' : ''}`;
        btn.innerHTML = `<span>${lang.flag}</span> <strong>${lang.native}</strong> <small>(${lang.name})</small>`;
        btn.onclick = () => selectLanguage(langKey);
        langChipsContainer.appendChild(btn);
    });

    const gestureGrid = document.getElementById('gestureButtonsGrid');
    GESTURES.forEach((g, idx) => {
        const btn = document.createElement('button');
        btn.className = `btn-gesture ${idx === 3 ? 'active' : ''} ${g.id === 0 ? 'btn-danger' : ''}`;
        btn.dataset.id = g.id;
        btn.innerHTML = `
            <span class="g-icon">${g.icon}</span>
            <span class="g-name">${g.name_en}</span>
            <span class="g-indic" id="gIndic_${g.id}">${g.phrases[activeLang].slice(0, 18)}...</span>
        `;
        btn.onclick = () => selectGesture(g.id);
        gestureGrid.appendChild(btn);
    });

    function selectLanguage(langKey) {
        activeLang = langKey;
        document.querySelectorAll('.lang-chip').forEach(c => c.classList.remove('active'));
        const activeChip = Array.from(document.querySelectorAll('.lang-chip')).find(c => c.textContent.includes(INDIC_LANGUAGES[langKey].name));
        if (activeChip) activeChip.classList.add('active');

        // Update all gesture card labels
        GESTURES.forEach(g => {
            const el = document.getElementById(`gIndic_${g.id}`);
            if (el) el.textContent = g.phrases[activeLang].slice(0, 18) + '...';
        });

        updateDisplayRibbon(currentGesture);
        speakCurrentPhrase();
    }

    function selectGesture(gid) {
        const g = GESTURES.find(item => item.id === gid);
        if (!g) return;
        currentGesture = g;
        targetJoints = g.joints;

        document.querySelectorAll('.btn-gesture').forEach(b => b.classList.remove('active'));
        const activeBtn = document.querySelector(`.btn-gesture[data-id="${gid}"]`);
        if (activeBtn) activeBtn.classList.add('active');

        updateDisplayRibbon(g);
        updateHardwareActuators(g);
        speakCurrentPhrase();
    }

    function updateDisplayRibbon(g) {
        document.getElementById('subtitleTextEn').textContent = `EN: "${g.name_en}"`;
        document.getElementById('subtitleTextIndic').textContent = `${activeLang.toUpperCase()}: "${g.phrases[activeLang]}"`;
        document.getElementById('subtitleConf').textContent = `[${g.id === 0 ? '99.8%' : '99.6%'}]`;
    }

    function updateHardwareActuators(g) {
        const r1 = document.getElementById('relay1Status');
        const r2 = document.getElementById('relay2Status');
        r1.textContent = g.relay1 ? 'ON' : 'OFF';
        r1.className = `act-val ${g.relay1 ? 'on' : 'off'}`;
        r2.textContent = g.relay2 ? 'ON' : 'OFF';
        r2.className = `act-val ${g.relay2 ? 'on' : 'off'}`;

        document.getElementById('servoStatus').textContent = `Pan: ${g.pan}° | Tilt: ${g.tilt}°`;
        document.getElementById('gsmStatus').textContent = g.gsm;

        drawLEDMatrix(g.matrixType);
    }

    // ── 4. Web Speech Synthesis in Indian Languages ─────────────────────────
    function speakCurrentPhrase() {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();

        const phrase = currentGesture.phrases[activeLang];
        const utterance = new SpeechSynthesisUtterance(phrase);
        utterance.lang = INDIC_LANGUAGES[activeLang].code;
        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        // Try to pick native voice if available
        const voices = window.speechSynthesis.getVoices();
        const nativeVoice = voices.find(v => v.lang.startsWith(activeLang) || v.lang.includes(INDIC_LANGUAGES[activeLang].code));
        if (nativeVoice) utterance.voice = nativeVoice;

        window.speechSynthesis.speak(utterance);
    }

    document.getElementById('btnSpeakVoice').onclick = speakCurrentPhrase;

    // ── 5. Canvas 60 FPS Hand Renderer ──────────────────────────────────────
    const canvas = document.getElementById('handCanvas');
    const ctx = canvas.getContext('2d');

    function animateCanvas() {
        ctx.fillStyle = '#05070d';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw Subtle Video Grid Guide
        drawCameraViewportGrid(ctx, canvas.width, canvas.height);

        // Interpolate Joints smoothly toward target pose
        const time = Date.now() * 0.003;
        for (let i = 0; i < 21; i++) {
            const jitterX = Math.sin(time + i) * 0.6;
            const jitterY = Math.cos(time + i * 1.5) * 0.6;
            currentJoints[i].x += (targetJoints[i].x + jitterX - currentJoints[i].x) * 0.18;
            currentJoints[i].y += (targetJoints[i].y + jitterY - currentJoints[i].y) * 0.18;
        }

        // Draw Bones (Connections)
        ctx.lineWidth = 4;
        HAND_CONNECTIONS.forEach(([startIdx, endIdx]) => {
            const p1 = currentJoints[startIdx];
            const p2 = currentJoints[endIdx];

            const grad = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
            grad.addColorStop(0, '#00f0ff');
            grad.addColorStop(1, '#00ff88');

            ctx.strokeStyle = grad;
            ctx.shadowColor = '#00f0ff';
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        });

        // Draw 21 Spherical Keypoint Joints
        currentJoints.forEach((j, idx) => {
            ctx.beginPath();
            ctx.arc(j.x, j.y, idx === 0 ? 8 : 5, 0, Math.PI * 2);
            ctx.fillStyle = idx === 0 ? '#ffb800' : (idx % 4 === 0 ? '#ff3366' : '#ffffff');
            ctx.shadowColor = ctx.fillStyle;
            ctx.shadowBlur = 12;
            ctx.fill();
        });

        requestAnimationFrame(animateCanvas);
    }
    requestAnimationFrame(animateCanvas);

    function drawCameraViewportGrid(ctx, w, h) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
        ctx.lineWidth = 1;
        ctx.shadowBlur = 0;
        for (let x = 0; x < w; x += 40) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let y = 0; y < h; y += 40) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }

        // Bounding Box
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.2)';
        ctx.strokeRect(30, 20, w - 60, h - 40);
        ctx.fillStyle = 'rgba(0, 240, 255, 0.6)';
        ctx.font = '11px monospace';
        ctx.fillText('TARGET: HAND_0 [TRACKING ACQUIRED]', 38, 38);
    }

    // ── 6. 8x13 LED Matrix Simulation ───────────────────────────────────────
    const matrixEl = document.getElementById('ledMatrix');
    for (let i = 0; i < 8 * 13; i++) {
        const dot = document.createElement('div');
        dot.className = 'led-dot';
        matrixEl.appendChild(dot);
    }

    function drawLEDMatrix(type) {
        const dots = document.querySelectorAll('.led-dot');
        dots.forEach(d => d.className = 'led-dot');

        if (type === 'sos') {
            dots.forEach((d, idx) => {
                if (idx % 2 === 0) d.classList.add('on', 'sos-flash');
            });
        } else if (type === 'check') {
            const checkPattern = [20, 33, 46, 59, 72, 60, 48, 36, 24];
            checkPattern.forEach(idx => {
                if (dots[idx]) dots[idx].classList.add('on');
            });
        } else if (type === 'relay_on') {
            const bulbPattern = [15, 16, 17, 28, 30, 41, 42, 43, 55, 68];
            bulbPattern.forEach(idx => {
                if (dots[idx]) dots[idx].classList.add('on');
            });
        }
    }

    // ── 7. Joint Kinematic Generators (15 Standard Poses) ────────────────────
    function getHandPoseWater() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-30, y: by-20}, {x: bx-45, y: by-45}, {x: bx-50, y: by-75}, {x: bx-55, y: by-105},
            {x: bx-20, y: by-60}, {x: bx-25, y: by-100}, {x: bx-30, y: by-130}, {x: bx-35, y: by-155},
            {x: bx, y: by-65}, {x: bx, y: by-105}, {x: bx, y: by-135}, {x: bx, y: by-165},
            {x: bx+20, y: by-60}, {x: bx+25, y: by-100}, {x: bx+30, y: by-130}, {x: bx+35, y: by-155},
            {x: bx+40, y: by-50}, {x: bx+48, y: by-80}, {x: bx+54, y: by-105}, {x: bx+60, y: by-125}
        ];
    }
    function getHandPoseOpenPalm() {
        const bx = 240, by = 240;
        return [
            {x: bx, y: by},
            {x: bx-40, y: by-25}, {x: bx-65, y: by-50}, {x: bx-85, y: by-80}, {x: bx-100, y: by-110},
            {x: bx-30, y: by-75}, {x: bx-40, y: by-120}, {x: bx-48, y: by-155}, {x: bx-55, y: by-190},
            {x: bx, y: by-80}, {x: bx, y: by-130}, {x: bx, y: by-170}, {x: bx, y: by-205},
            {x: bx+30, y: by-75}, {x: bx+40, y: by-120}, {x: bx+48, y: by-155}, {x: bx+55, y: by-190},
            {x: bx+60, y: by-65}, {x: bx+75, y: by-100}, {x: bx+88, y: by-130}, {x: bx+98, y: by-160}
        ];
    }
    function getHandPoseFist() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-25, y: by-15}, {x: bx-35, y: by-30}, {x: bx-20, y: by-45}, {x: bx-5, y: by-48},
            {x: bx-25, y: by-40}, {x: bx-25, y: by-65}, {x: bx-15, y: by-55}, {x: bx-10, y: by-45},
            {x: bx-5, y: by-45}, {x: bx-5, y: by-70}, {x: bx+2, y: by-60}, {x: bx+5, y: by-50},
            {x: bx+15, y: by-40}, {x: bx+15, y: by-65}, {x: bx+18, y: by-55}, {x: bx+18, y: by-45},
            {x: bx+32, y: by-35}, {x: bx+32, y: by-55}, {x: bx+30, y: by-48}, {x: bx+28, y: by-40}
        ];
    }
    function getHandPoseThanks() {
        const bx = 240, by = 230;
        return [
            {x: bx, y: by},
            {x: bx-20, y: by-25}, {x: bx-30, y: by-50}, {x: bx-35, y: by-75}, {x: bx-40, y: by-100},
            {x: bx-15, y: by-70}, {x: bx-18, y: by-115}, {x: bx-20, y: by-150}, {x: bx-22, y: by-185},
            {x: bx, y: by-75}, {x: bx, y: by-120}, {x: bx, y: by-160}, {x: bx, y: by-195},
            {x: bx+15, y: by-70}, {x: bx+18, y: by-115}, {x: bx+20, y: by-150}, {x: bx+22, y: by-185},
            {x: bx+30, y: by-60}, {x: bx+35, y: by-95}, {x: bx+40, y: by-125}, {x: bx+45, y: by-150}
        ];
    }
    function getHandPoseThumbsUp() {
        const bx = 240, by = 230;
        return [
            {x: bx, y: by},
            {x: bx-30, y: by-30}, {x: bx-45, y: by-70}, {x: bx-50, y: by-120}, {x: bx-55, y: by-165},
            {x: bx-15, y: by-35}, {x: bx-15, y: by-60}, {x: bx-5, y: by-50}, {x: bx, y: by-40},
            {x: bx+5, y: by-40}, {x: bx+5, y: by-65}, {x: bx+12, y: by-55}, {x: bx+15, y: by-45},
            {x: bx+25, y: by-35}, {x: bx+25, y: by-60}, {x: bx+28, y: by-50}, {x: bx+28, y: by-40},
            {x: bx+40, y: by-30}, {x: bx+40, y: by-50}, {x: bx+38, y: by-42}, {x: bx+35, y: by-35}
        ];
    }
    function getHandPoseSOS() {
        const bx = 240, by = 230;
        return [
            {x: bx, y: by},
            {x: bx-50, y: by-30}, {x: bx-85, y: by-60}, {x: bx-110, y: by-95}, {x: bx-130, y: by-130},
            {x: bx-38, y: by-85}, {x: bx-52, y: by-135}, {x: bx-62, y: by-175}, {x: bx-72, y: by-215},
            {x: bx, y: by-90}, {x: bx, y: by-145}, {x: bx, y: by-190}, {x: bx, y: by-230},
            {x: bx+38, y: by-85}, {x: bx+52, y: by-135}, {x: bx+62, y: by-175}, {x: bx+72, y: by-215},
            {x: bx+70, y: by-70}, {x: bx+90, y: by-110}, {x: bx+105, y: by-145}, {x: bx+118, y: by-178}
        ];
    }
    function getHandPoseNo() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-25, y: by-15}, {x: bx-35, y: by-30}, {x: bx-20, y: by-45}, {x: bx-5, y: by-48},
            {x: bx-20, y: by-60}, {x: bx-25, y: by-105}, {x: bx-30, y: by-145}, {x: bx-35, y: by-185}, // Index up
            {x: bx+5, y: by-40}, {x: bx+5, y: by-65}, {x: bx+12, y: by-55}, {x: bx+15, y: by-45},
            {x: bx+25, y: by-35}, {x: bx+25, y: by-60}, {x: bx+28, y: by-50}, {x: bx+28, y: by-40},
            {x: bx+40, y: by-30}, {x: bx+40, y: by-50}, {x: bx+38, y: by-42}, {x: bx+35, y: by-35}
        ];
    }
    function getHandPosePinch() {
        const bx = 240, by = 220;
        const px = bx, py = by - 120;
        return [
            {x: bx, y: by},
            {x: bx-20, y: by-25}, {x: bx-30, y: by-55}, {x: bx-20, y: by-90}, {x: px, y: py},
            {x: bx-15, y: by-50}, {x: bx-15, y: by-85}, {x: bx-10, y: by-105}, {x: px, y: py},
            {x: bx, y: by-55}, {x: bx, y: by-90}, {x: bx, y: by-110}, {x: px, y: py},
            {x: bx+15, y: by-50}, {x: bx+15, y: by-85}, {x: bx+10, y: by-105}, {x: px, y: py},
            {x: bx+30, y: by-40}, {x: bx+30, y: by-70}, {x: bx+20, y: by-95}, {x: px, y: py}
        ];
    }
    function getHandPoseMedicine() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-20, y: by-30}, {x: bx-25, y: by-65}, {x: bx-15, y: by-95}, {x: bx-5, y: by-110},
            {x: bx-15, y: by-50}, {x: bx-15, y: by-85}, {x: bx-10, y: by-105}, {x: bx-5, y: by-110},
            {x: bx, y: by-45}, {x: bx, y: by-70}, {x: bx+5, y: by-60}, {x: bx+8, y: by-50},
            {x: bx+18, y: by-40}, {x: bx+18, y: by-65}, {x: bx+20, y: by-55}, {x: bx+20, y: by-45},
            {x: bx+32, y: by-35}, {x: bx+32, y: by-55}, {x: bx+30, y: by-48}, {x: bx+28, y: by-40}
        ];
    }
    function getHandPoseTremor() {
        const bx = 240, by = 220;
        return getHandPoseFist().map((pt, i) => ({
            x: pt.x + (Math.random() - 0.5) * 8,
            y: pt.y + (Math.random() - 0.5) * 8
        }));
    }
    function getHandPoseFan() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-25, y: by-15}, {x: bx-35, y: by-30}, {x: bx-20, y: by-45}, {x: bx-5, y: by-48},
            {x: bx-20, y: by-60}, {x: bx-30, y: by-105}, {x: bx-40, y: by-145}, {x: bx-50, y: by-185}, // Index
            {x: bx+5, y: by-65}, {x: bx+10, y: by-110}, {x: bx+15, y: by-150}, {x: bx+20, y: by-190},  // Middle
            {x: bx+25, y: by-35}, {x: bx+25, y: by-60}, {x: bx+28, y: by-50}, {x: bx+28, y: by-40},
            {x: bx+40, y: by-30}, {x: bx+40, y: by-50}, {x: bx+38, y: by-42}, {x: bx+35, y: by-35}
        ];
    }
    function getHandPoseWashroom() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-25, y: by-15}, {x: bx-15, y: by-45}, {x: bx, y: by-70}, {x: bx-10, y: by-90}, // Thumb tucked
            {x: bx-20, y: by-40}, {x: bx-20, y: by-65}, {x: bx-15, y: by-55}, {x: bx-10, y: by-45},
            {x: bx-5, y: by-45}, {x: bx-5, y: by-70}, {x: bx+2, y: by-60}, {x: bx+5, y: by-50},
            {x: bx+15, y: by-40}, {x: bx+15, y: by-65}, {x: bx+18, y: by-55}, {x: bx+18, y: by-45},
            {x: bx+32, y: by-35}, {x: bx+32, y: by-55}, {x: bx+30, y: by-48}, {x: bx+28, y: by-40}
        ];
    }
    function getHandPosePhone() {
        const bx = 240, by = 220;
        return [
            {x: bx, y: by},
            {x: bx-40, y: by-30}, {x: bx-70, y: by-60}, {x: bx-90, y: by-95}, {x: bx-110, y: by-130}, // Thumb out
            {x: bx-15, y: by-35}, {x: bx-15, y: by-60}, {x: bx-5, y: by-50}, {x: bx, y: by-40},
            {x: bx+5, y: by-40}, {x: bx+5, y: by-65}, {x: bx+12, y: by-55}, {x: bx+15, y: by-45},
            {x: bx+25, y: by-35}, {x: bx+25, y: by-60}, {x: bx+28, y: by-50}, {x: bx+28, y: by-40},
            {x: bx+45, y: by-40}, {x: bx+70, y: by-75}, {x: bx+90, y: by-110}, {x: bx+110, y: by-145}  // Pinky out
        ];
    }
    function getHandPoseSleep() {
        const bx = 240, by = 230;
        return [
            {x: bx, y: by},
            {x: bx-30, y: by-15}, {x: bx-50, y: by-30}, {x: bx-70, y: by-45}, {x: bx-85, y: by-60},
            {x: bx-25, y: by-40}, {x: bx-50, y: by-70}, {x: bx-70, y: by-95}, {x: bx-90, y: by-120},
            {x: bx, y: by-45}, {x: bx-20, y: by-75}, {x: bx-40, y: by-105}, {x: bx-60, y: by-130},
            {x: bx+25, y: by-40}, {x: bx+10, y: by-70}, {x: bx-5, y: by-95}, {x: bx-25, y: by-120},
            {x: bx+45, y: by-30}, {x: bx+35, y: by-55}, {x: bx+20, y: by-80}, {x: bx+5, y: by-100}
        ];
    }

    // Initial state
    selectGesture(3);
});
