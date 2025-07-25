"use client";
import Link from "next/link";
import styles from "./page.module.scss";
import ErrorLogger from "@/components/ErrorLogger";

export default function Home() {
  return (
    <>
      <ErrorLogger />
      <div className={styles.container}>
        <div className={styles.content}>
          <h1 className={styles.title}>App Pulse</h1>
          <p className={styles.subtitle}>
            Service & Web Application Monitoring
          </p>

          <div className={styles.buttonContainer}>
            <Link href="/user" className={styles.button}>
              User
            </Link>
            <Link href="/developer" className={styles.button}>
              Developer
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
