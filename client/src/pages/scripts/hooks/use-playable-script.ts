import { useQuery } from "react-query";
import { getPlayableScript } from "../../../api";
import { useCallback, useMemo } from "react";
import { getWSBaseURL } from "../../../api/get-base-url";
import useWebSocket, { ReadyState } from "react-use-websocket";

export type PlayableScriptStatus = "READY" | "WAITING";

export type PlayableScriptKey = "UP" | "DOWN" | "LEFT" | "RIGHT";
type WSResponse =
  | {
      type: "error";
      data: string;
    }
  | {
      type: "status";
      data: PlayableScriptStatus;
    };

export const usePlayableScript = ({ scriptId }: { scriptId: string }) => {
  const socketURL = useMemo(() => {
    return `${getWSBaseURL()}/ws`;
  }, []);

  const { readyState, sendJsonMessage, lastJsonMessage } =
    useWebSocket<WSResponse | null>(socketURL);

  const { data, isLoading } = useQuery({
    queryKey: ["playable-script", { scriptId }],
    queryFn: () => getPlayableScript({ path: { script_id: scriptId } }),
  });

  const choosePlayer = useCallback(
    (playerNumber: number) => {
      sendJsonMessage({
        type: "choose_player",
        data: { player_number: playerNumber },
      });
    },
    [sendJsonMessage]
  );

  const sendKey = useCallback(
    (key: PlayableScriptKey) => {
      sendJsonMessage({
        type: "key",
        data: { key },
      });
    },
    [sendJsonMessage]
  );

  return {
    isLoading: isLoading || readyState !== ReadyState.OPEN,
    keys: data?.data?.keys,
    minPlayers: data?.data?.min_player_number,
    maxPlayers: data?.data?.max_player_number,
    status:
      lastJsonMessage?.type === "status" ? lastJsonMessage.data : "WAITING",
    choosePlayer,
    sendKey,
  };
};
