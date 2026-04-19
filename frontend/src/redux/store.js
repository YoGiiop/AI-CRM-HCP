import { configureStore, createSlice } from "@reduxjs/toolkit";

const initialInteraction = {
  id: null,
  hcp_name: "",
  interaction_type: "",
  date: "",
  time: "",
  attendees: "",
  topics: "",
  materials_shared: [],
  samples_distributed: [],
  sentiment: "",
  outcomes: "",
  follow_up: "",
  ai_suggested_follow_up: [],
  summary: "",
  insight: "",
  priority: "",
};

const interactionSlice = createSlice({
  name: "interaction",
  initialState: initialInteraction,
  reducers: {
    updateInteraction: (state, action) => {
      const nextState = { ...state, ...action.payload };

      nextState.materials_shared = normalizeList(nextState.materials_shared);
      nextState.samples_distributed = normalizeList(nextState.samples_distributed);
      nextState.ai_suggested_follow_up = normalizeList(nextState.ai_suggested_follow_up);

      return nextState;
    },
    resetInteraction: () => initialInteraction,
  },
});

function normalizeList(value) {
  if (Array.isArray(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim()) {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }

  return [];
}

export const { updateInteraction, resetInteraction } = interactionSlice.actions;

export const store = configureStore({
  reducer: {
    interaction: interactionSlice.reducer,
  },
});