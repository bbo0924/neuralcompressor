from argparse import ArgumentParser
import numpy as np
import torch
import sys
from nncompress import EmbeddingCompressor
from nncompress import Trainer


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--embeddings", default="data/glove/glove.6B.50d.txt")
    parser.add_argument("--model", default="data/model")
    parser.add_argument("--prefix",  default="data/model")
    parser.add_argument("-m", "--num_codebooks", default=64, type=int)
    parser.add_argument("--lr", default=1e-4, type=float)
    parser.add_argument("-k", "--num_vectors", default=16, type=int)
    parser.add_argument("-d", "--embedding_dim", default=384, type=int)
    parser.add_argument("-s", "--num_embeddings", default=75960, type=int)
    parser.add_argument("--batch_size", default=64, type=int)
    parser.add_argument("--epochs", default=240, type=int)
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--use_gpu", action="store_true")
    # parser.add_argument("--sample_words", nargs="+",
    #                     default=["dog", "dogs", "man", "woman", "king", "queen"])
    parser.add_argument("-ckpt", "--checkpoint")
    args = parser.parse_args()
    compressor = EmbeddingCompressor(
        args.embedding_dim, args.num_codebooks, args.num_vectors, use_gpu=args.use_gpu)
    if args.use_gpu:
        print("Using CUDA ... ", file=sys.stderr)
        compressor = compressor.cuda()
    if args.train:
        trainer = Trainer(compressor, args.num_embeddings,
                          args.embedding_dim, args.model, lr=args.lr, use_gpu=args.use_gpu, batch_size=args.batch_size)

        trainer.load_pretrained_embeddings(args.embeddings)
        trainer.run(max_epochs=args.epochs)
        torch.save(compressor.state_dict(), args.model + ".pt")
    elif args.export:
        compressor.load_state_dict(torch.load(args.model + ".pt"))

        trainer = Trainer(compressor, args.num_embeddings,
                          args.embedding_dim, args.model, use_gpu=args.use_gpu, batch_size=args.batch_size)
        trainer.load_pretrained_embeddings(args.embeddings)
        trainer.export(args.prefix, args.sample_words)
    elif args.evaluate:
        compressor.load_state_dict(torch.load(args.model + ".pt"))

        trainer = Trainer(compressor, args.num_embeddings,
                          args.embedding_dim, args.model, use_gpu=args.use_gpu, batch_size=args.batch_size)
        trainer.load_pretrained_embeddings(args.embeddings)
        distance = trainer.evaluate()
        # np.savetxt('data/glove/reconstructed.6B.50d.txt', reconstructed.detach().numpy())
        print("Mean euclidean distance:", distance)
    elif args.extract:
        ckpt = torch.load(args.checkpoint)
        input_pretrained_embedding = ckpt["model"]["encoder.embed_tokens.weight"]
        if args.use_gpu:
            np.savetxt('input_pretrained_embedding.txt', input_pretrained_embedding.cpu().numpy())
        else:
            np.savetxt('input_pretrained_embedding.txt', input_pretrained_embedding.numpy())
