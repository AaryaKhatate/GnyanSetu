/**
 * TTS Controller - Text-to-Speech functionality using Web Speech API
 * 
 * Provides synchronized audio narration for teaching sessions
 */

const synth = window.speechSynthesis;
let currentUtterance = null;
let isSpeakingState = false;

/**
 * Speak text with TTS
 * @param {string} text - Text to speak
 * @param {Function} onEndCallback - Callback when speech ends
 * @param {Object} options - TTS options (rate, pitch, volume, voice)
 */
export function speak(text, onEndCallback, options = {}) {
    if (!synth) {
        console.warn('Speech synthesis not supported');
        if (onEndCallback) onEndCallback();
        return;
    }
    
    // Cancel any ongoing speech
    if (currentUtterance && synth.speaking) {
        synth.cancel();
    }
    
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.lang = options.lang || 'en-US';
    currentUtterance.rate = options.rate || 0.9; // Slightly slower for clarity
    currentUtterance.pitch = options.pitch || 1.0;
    currentUtterance.volume = options.volume || 1.0;
    
    // Set voice if specified
    if (options.voice) {
        const voices = synth.getVoices();
        const selectedVoice = voices.find(v => v.name === options.voice);
        if (selectedVoice) {
            currentUtterance.voice = selectedVoice;
        }
    }
    
    currentUtterance.onstart = () => {
        isSpeakingState = true;
        console.log('🔊 TTS started');
        if (options.onStart) options.onStart();
    };
    
    currentUtterance.onend = () => {
        isSpeakingState = false;
        console.log('🔇 TTS ended');
        if (onEndCallback) onEndCallback();
    };
    
    currentUtterance.onerror = (err) => {
        isSpeakingState = false;
        console.error('❌ TTS error:', err);
        if (onEndCallback) onEndCallback();
    };
    
    synth.speak(currentUtterance);
}

/**
 * Stop current speech
 */
export function stopSpeaking() {
    if (synth && synth.speaking) {
        synth.cancel();
    }
    isSpeakingState = false;
    console.log('⏹️ TTS stopped');
}

/**
 * Pause current speech
 */
export function pauseSpeaking() {
    if (synth && synth.speaking) {
        synth.pause();
        console.log('⏸️ TTS paused');
    }
}

/**
 * Resume paused speech
 */
export function resumeSpeaking() {
    if (synth && synth.paused) {
        synth.resume();
        console.log('▶️ TTS resumed');
    }
}

/**
 * Check if currently speaking
 * @returns {boolean}
 */
export function isSpeaking() {
    return isSpeakingState || (synth && synth.speaking);
}

/**
 * Get available voices
 * @returns {Array} List of available voices
 */
export function getVoices() {
    return synth ? synth.getVoices() : [];
}

/**
 * Get preferred voice (English female if available)
 * @returns {SpeechSynthesisVoice|null}
 */
export function getPreferredVoice() {
    const voices = getVoices();
    
    // Prefer English female voices
    const femaleEnglishVoice = voices.find(v => 
        v.lang.startsWith('en') && v.name.toLowerCase().includes('female')
    );
    
    if (femaleEnglishVoice) return femaleEnglishVoice;
    
    // Fallback to any English voice
    const englishVoice = voices.find(v => v.lang.startsWith('en'));
    if (englishVoice) return englishVoice;
    
    // Fallback to first available voice
    return voices[0] || null;
}

export default {
    speak,
    stopSpeaking,
    pauseSpeaking,
    resumeSpeaking,
    isSpeaking,
    getVoices,
    getPreferredVoice
};
