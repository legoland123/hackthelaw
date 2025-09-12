// Import the functions you need from the SDKs you need
//import { initializeApp } from "firebase/app";
//import { getAnalytics } from "firebase/analytics";
//import { getFirestore } from "firebase/firestore";
//import { getStorage } from "firebase/storage";
//import { getAuth } from "firebase/auth";
//
//// Your web app's Firebase configuration
//// For Firebase JS SDK v7.20.0 and later, measurementId is optional
//const firebaseConfig = {
//    apiKey: "AIzaSyCm1L0JLDH_5-hRCZoQJ-2N4xsft0PYFS0",
//    authDomain: "hackthelaw-smulit-4fec4.firebaseapp.com",
//    projectId: "hackthelaw-smulit-4fec4",
//    storageBucket: "hackthelaw-smulit-4fec4.firebasestorage.app",
//    messagingSenderId: "423327249710",
//    appId: "1:423327249710:web:4aae1b38b1ede02328f6bf",
//    measurementId: "G-TLD4KFCZS9"
//};
//
//// Initialize Firebase
//const app = initializeApp(firebaseConfig);
//
//// Initialize Firebase services
//const analytics = getAnalytics(app);
//const db = getFirestore(app);
//const storage = getStorage(app);
//const auth = getAuth(app);
//
//export { app, analytics, db, storage, auth }; 
// src/firebase/config.js
import { initializeApp } from "firebase/app";
import {
  getAuth,
  onAuthStateChanged,
  signInAnonymously,
} from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

/** Make sure we have a Firebase user before any read/write */
export async function ensureAuth() {
  if (auth.currentUser) return auth.currentUser;

  return await new Promise((resolve, reject) => {
    const off = onAuthStateChanged(auth, async (user) => {
      off();
      try {
        if (user) return resolve(user);
        const cred = await signInAnonymously(auth);
        resolve(cred.user);
      } catch (e) {
        reject(e);
      }
    });
  });
}
