import { Button, Flex, Input, Kbd, Loader, Title } from "@mantine/core";
import {
  PlayableScriptKey,
  PlayableScriptStatus,
  usePlayableScript,
} from "../hooks/use-playable-script";
import { useState } from "react";

export const PlayableScript = ({
  scriptId,
  scriptName,
}: {
  scriptId: string;
  scriptName: string;
}) => {
  const {
    isLoading,
    minPlayers,
    choosePlayer,
    maxPlayers,
    status,
    sendKey,
    keys,
  } = usePlayableScript({
    scriptId,
  });

  return (
    <>
      <Title pt="lg" pb="sm">
        {scriptName.toUpperCase()}
      </Title>
      {isLoading ? (
        <Loader />
      ) : (
        <>
          <PlayableScriptsDetails
            minPlayers={minPlayers!}
            maxPlayers={maxPlayers!}
            status={status}
          />
          <PlayableScriptControl
            keys={keys as PlayableScriptKey[]}
            maxPlayers={maxPlayers!}
            sendKey={sendKey}
            status={status}
            choosePlayer={choosePlayer}
          />
        </>
      )}
    </>
  );
};

const PlayableScriptsDetails = ({
  minPlayers,
  maxPlayers,
  status,
}: {
  minPlayers: number;
  maxPlayers: number;
  status: string;
}) => {
  return (
    <div>
      <div>Min players: {minPlayers}</div>
      <div>Max players: {maxPlayers}</div>
      <div>Status: {status}</div>
    </div>
  );
};

const PlayableScriptControl = ({
  maxPlayers,
  sendKey,
  status,
  keys,
  choosePlayer,
}: {
  maxPlayers: number;
  status: PlayableScriptStatus;
  keys: PlayableScriptKey[];
  sendKey: (key: PlayableScriptKey) => void;
  choosePlayer: (playerNumber: number) => void;
}) => {
  return (
    <div>
      <PlayerSelection maxPlayers={maxPlayers} choosePlayer={choosePlayer} />
      {status === "READY" && <PlayerControl sendKey={sendKey} keys={keys} />}
    </div>
  );
};

const PlayerSelection = ({
  maxPlayers,
  choosePlayer,
}: {
  maxPlayers: number;
  choosePlayer: (playerNumber: number) => void;
}) => {
  return (
    <>
      <Title pt="lg" pb="sm" order={2}>
        Select a player
      </Title>
      <Flex
        gap="md"
        justify="flex-start"
        align="flex-start"
        direction="row"
        wrap="wrap"
      >
        {Array.from({ length: maxPlayers }).map((_, index) => (
          <Button key={index} onClick={() => choosePlayer(index + 1)}>
            P{index + 1}
          </Button>
        ))}
      </Flex>
    </>
  );
};

const PlayerControl = ({
  sendKey,
  keys,
}: {
  sendKey: (key: PlayableScriptKey) => void;
  keys: PlayableScriptKey[];
}) => {
  return (
    <>
      <Title pt="lg" pb="sm" order={2}>
        Control the player
      </Title>
      <Flex
        gap="md"
        justify="flex-start"
        align="flex-start"
        direction="column"
        wrap="wrap"
      >
        <Flex gap="md" justify="flex-start" align="flex-start" wrap="wrap">
          {keys.map((key) => (
            <Kbd>{key}</Kbd>
          ))}
        </Flex>
        <Input
          autoFocus
          onKeyDown={(event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.key === "ArrowUp") {
              sendKey("UP");
            }
            if (event.key === "ArrowDown") {
              sendKey("DOWN");
            }
            if (event.key === "ArrowLeft") {
              sendKey("LEFT");
            }
            if (event.key === "ArrowRight") {
              sendKey("RIGHT");
            }
          }}
          placeholder="Press keys here to control"
        />
      </Flex>
    </>
  );
};
