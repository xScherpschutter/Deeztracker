import { invoke } from "@tauri-apps/api/core";

export class AuthService {
  static async login(arl: string): Promise<boolean> {
    try {
      return await invoke<boolean>("login", { arl });
    } catch (error) {
      console.error("Login Error:", error);
      return false;
    }
  }
}
