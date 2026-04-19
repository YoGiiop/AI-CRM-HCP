import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import App from "./App";
import { store } from "./redux/store";

test("renders the interaction form and chat panel", () => {
  render(
    <Provider store={store}>
      <App />
    </Provider>
  );

  expect(screen.getByText(/log hcp interaction/i)).toBeInTheDocument();
  expect(screen.getByText(/ai assistant/i)).toBeInTheDocument();
});
