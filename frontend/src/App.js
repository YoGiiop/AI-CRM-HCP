import Chat from "./components/Chat";
import Form from "./components/Form";
import "./App.css";

function App() {
  return (
    <main className="app-shell">
      <section className="screen-card">
        <div className="screen-grid">
          <div className="screen-column screen-column-wide">
            <Form />
          </div>

          <div className="screen-column screen-column-chat">
            <Chat />
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;