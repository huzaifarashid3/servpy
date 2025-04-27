import React, { useState } from "react";
import "./App.css";
import MicroserviceList from "./MicroserviceList";

function App() {
  const [page, setPage] = useState("upload");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");

  if (page === "list") {
    return <MicroserviceList onBack={() => setPage("upload")} />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    setStatus("Uploading...");
    try {
      const res = await fetch("http://localhost:8000/upload-microservice", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.status === "success") {
        setStatus("Upload successful!");
      } else {
        setStatus("Upload failed.");
      }
    } catch (err) {
      setStatus(`Error uploading. ${err.message}`);
    }
  };

  return (
    <div className="App">
      <button
        className="nav-btn"
        onClick={() => setPage("list")}
      >
        View Uploaded Microservices
      </button>
      <h1>Upload Microservice</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Microservice Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <br />
        <textarea
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <br />
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(e.target.files)}
          required
        />
        <br />
        <button type="submit">Upload</button>
      </form>
      <p>{status}</p>
    </div>
  );
}

export default App;
