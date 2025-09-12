// src/firebase/services.js
import {
  collection,
  doc,
  getDocs,
  getDoc,
  addDoc,
  updateDoc,
  deleteDoc,
  query,
  orderBy,
  where,
  serverTimestamp,
  arrayUnion,
} from "firebase/firestore";
import {
  ref,
  uploadBytesResumable,
  getDownloadURL,
  deleteObject,
} from "firebase/storage";

import { db, storage, ensureAuth } from "./config";

// ---------- Collection names ----------
const COLLECTIONS = {
  PROJECTS: "projects",
  DOCUMENTS: "documents",
  CONFLICTS: "conflicts",
};

// ---------- Project Services ----------
export const projectServices = {
  async getAllProjects() {
    await ensureAuth();
    const q = query(
      collection(db, COLLECTIONS.PROJECTS),
      orderBy("lastUpdated", "desc")
    );
    const snap = await getDocs(q);
    return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  },

  async getProjectById(projectId) {
    await ensureAuth();
    const ref = doc(db, COLLECTIONS.PROJECTS, projectId);
    const snap = await getDoc(ref);
    if (!snap.exists()) throw new Error("Project not found");
    return { id: snap.id, ...snap.data() };
  },

  async createProject(projectData) {
    await ensureAuth();
    const projectWithTimestamp = {
      ...projectData,
      createdAt: serverTimestamp(),
      lastUpdated: serverTimestamp(),
      documentIds: [],
      conflicts: [],
    };
    const ref = await addDoc(
      collection(db, COLLECTIONS.PROJECTS),
      projectWithTimestamp
    );
    return { id: ref.id, ...projectWithTimestamp };
  },

  async updateProject(projectId, updateData) {
    await ensureAuth();
    const ref = doc(db, COLLECTIONS.PROJECTS, projectId);
    await updateDoc(ref, { ...updateData, lastUpdated: serverTimestamp() });
    return await this.getProjectById(projectId);
  },

  async deleteProject(projectId) {
    await ensureAuth();
    const documents = await documentServices.getDocumentsByProjectId(projectId);
    const conflicts = await conflictServices.getConflictsByProjectId(projectId);

    for (const d of documents) await documentServices.deleteDocument(d.id);
    for (const c of conflicts) await conflictServices.deleteConflict(c.id);

    await deleteDoc(doc(db, COLLECTIONS.PROJECTS, projectId));
    return true;
  },
};

// ---------- Document Services ----------
export const documentServices = {
  async getDocumentsByProjectId(projectId) {
    await ensureAuth();
    const q = query(
      collection(db, COLLECTIONS.DOCUMENTS),
      where("projectId", "==", projectId),
      orderBy("timestamp", "desc")
    );
    const snap = await getDocs(q);
    return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  },

  async getDocumentById(documentId) {
    await ensureAuth();
    const ref = doc(db, COLLECTIONS.DOCUMENTS, documentId);
    const snap = await getDoc(ref);
    return snap.exists() ? { id: snap.id, ...snap.data() } : null;
  },

  uploadDocumentFile(file, projectId, onProgress) {
    const fileName = `${projectId}/${Date.now()}_${file.name}`;
    const storageRef = ref(storage, `documents/${fileName}`);
    const task = uploadBytesResumable(storageRef, file);

    return new Promise((resolve, reject) => {
      task.on(
        "state_changed",
        (s) => onProgress?.((s.bytesTransferred / s.totalBytes) * 100),
        reject,
        async () => {
          try {
            const downloadURL = await getDownloadURL(task.snapshot.ref);
            resolve({
              fileName,
              downloadURL,
              size: file.size,
              type: file.type,
            });
          } catch (e) {
            reject(e);
          }
        }
      );
    });
  },

  async createDocument(projectId, documentData, file = null, onProgress) {
    await ensureAuth();

    let fileInfo = null;
    if (file) fileInfo = await this.uploadDocumentFile(file, projectId, onProgress);

    const payload = {
      ...documentData,
      projectId,
      timestamp: serverTimestamp(),
      fileInfo,
      conflicts: [],
    };

    const newRef = await addDoc(collection(db, COLLECTIONS.DOCUMENTS), payload);

    // update project with new doc id
    const projectRef = doc(db, COLLECTIONS.PROJECTS, projectId);
    await updateDoc(projectRef, {
      documentIds: arrayUnion(newRef.id),
      lastUpdated: serverTimestamp(),
    });

    const created = await getDoc(newRef);
    return { id: created.id, ...created.data() };
  },

  async updateDocument(documentId, updateData) {
    await ensureAuth();
    await updateDoc(doc(db, COLLECTIONS.DOCUMENTS, documentId), updateData);
    return await this.getDocumentById(documentId);
  },

  async deleteDocument(documentId) {
    await ensureAuth();
    const asIs = await this.getDocumentById(documentId);

    if (asIs?.fileInfo?.fileName) {
      await deleteObject(ref(storage, `documents/${asIs.fileInfo.fileName}`));
    }

    await deleteDoc(doc(db, COLLECTIONS.DOCUMENTS, documentId));
    return true;
  },
};

// ---------- Conflict Services ----------
export const conflictServices = {
  async getConflictsByProjectId(projectId) {
    await ensureAuth();
    const q = query(
      collection(db, COLLECTIONS.CONFLICTS),
      where("projectId", "==", projectId),
      orderBy("createdAt", "desc")
    );
    const snap = await getDocs(q);
    return snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  },

  async createConflict(projectId, conflictData) {
    await ensureAuth();
    const payload = {
      ...conflictData,
      projectId,
      createdAt: serverTimestamp(),
      status: "open",
    };
    const ref = await addDoc(collection(db, COLLECTIONS.CONFLICTS), payload);
    return { id: ref.id, ...payload };
  },

  async updateConflict(conflictId, updateData) {
    await ensureAuth();
    const ref = doc(db, COLLECTIONS.CONFLICTS, conflictId);
    await updateDoc(ref, updateData);
    const snap = await getDoc(ref);
    return { id: snap.id, ...snap.data() };
  },

  async resolveConflict(conflictId, resolution) {
    await ensureAuth();
    return await this.updateConflict(conflictId, {
      status: "resolved",
      resolution,
      resolvedAt: serverTimestamp(),
    });
  },

  async deleteConflict(conflictId) {
    await ensureAuth();
    await deleteDoc(doc(db, COLLECTIONS.CONFLICTS, conflictId));
    return true;
  },
};
